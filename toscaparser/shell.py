#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import argparse
import os
import sys

from toscaparser.tosca_template import ToscaTemplate
from toscaparser.common.exception import TOSCAException
from toscaparser.utils.gettextutils import _
import toscaparser.utils.urlutils
import numpy as np
from pyfancy import *

"""
CLI entry point to show how TOSCA Parser can be used programmatically

This is a basic command line utility showing the entry point in the
TOSCA Parser and how to iterate over parsed template. It can be extended
or modified to fit an individual need.

It can be used as,
#tosca-parser --template-file=<path to the YAML template>
#tosca-parser --template-file=<path to the CSAR zip file>
#tosca-parser --template-file=<URL to the template or CSAR>

e.g.
#tosca-parser
 --template-file=toscaparser/tests/data/tosca_helloworld.yaml
#tosca-parser
 --template-file=toscaparser/tests/data/CSAR/csar_hello_world.zip
"""


class ParserShell(object):

    def get_parser(self, argv):
        parser = argparse.ArgumentParser(prog="tosca-parser")
        parser.add_argument('-v', '--version',
                            action='store_true',
                            help=_('show tool version.'))
        parser.add_argument('-x', '--verbose',
                            action='store_true',
                            help=_('display each FP matrix'))
        parser.add_argument('-d', '--diff',
                            action='store_true',
                            help=_('display each matrix'))
        parser.add_argument('-c', '--template-file',
                            metavar='<filename>',
                            help=_('YAML template or CSAR file to parse.'))

        return parser
    def main(self, argv):
        parser = self.get_parser(argv)
        (args, extra_args) = parser.parse_known_args(argv)
        path = args.template_file
        if (args.version):
            print("v1.0.0")
            exit(0)
        if (not args.template_file):
            if (os.path.isfile('./tosca-conf.yml')):
                path = './tosca-conf.yml'
            else:
                print("\nCould not found default config file: `./tosca-conf.yml`")
                print("")
                print("  to provide explicitly the path please use `-c`")
                print("  e.g. tosca-parser -c ./my-template.yaml")
                print("")
                print("  to display default help use `--help`")
                print("")
                exit(1)
        if os.path.isfile(path):
            try:
                self.parse(path, args)
            except TOSCAException as err:
                print("\nCould not parse yaml field.")
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print(err)
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        elif toscaparser.utils.urlutils.UrlUtils.validate_url(path):
            self.parse(path, args, False)
        else:
            raise ValueError(_('"%(path)s" is not a valid file.')
                            % {'path': path})

    def connectivityGraph(self, tosca):
        if not hasattr(tosca, 'nodetemplates'):
            return
        nodetemplates = tosca.nodetemplates
        _cps = filter(lambda x: x.type == "tosca.nodes.nfv.CP", nodetemplates)
        _cps = map(lambda x: {
            "name": x.name,
            "requirements": x.requirements,
            "link": filter(lambda y: y.has_key('virtualLink'), x.requirements)
            }, _cps)
        _cps = map(lambda x: {
            "name": x['name'],
            "requirements": x['requirements'],
            "link": x['link'][0]['virtualLink'] if (len(x['link']) > 0) else ""
            }, _cps)
        _cpsd = {}
        for cp in _cps:
            _cpsd[cp['name']] = cp
        connectivity = []
        cpsItems = sorted(_cpsd.items(), key=lambda x: x[0])
        total_cps = len(cpsItems)
        for cp in cpsItems:
            connectivity.append([0] * total_cps)
        for r in range(0, total_cps):
            for c in range(0, total_cps):
                if r == c:
                    connectivity[r][c] = 0
                else:
                    cpfrom = cpsItems[r][0]
                    cpto = cpsItems[c][0]
                    if _cpsd[cpfrom]['link'] == _cpsd[cpto]['link']:
                        # print cpfrom, '->', cpto, '(', r, ',', c,')'
                        connectivity[r][c] = 1
        return { "cpsItems": cpsItems, "connectivity": connectivity }

    def printMatrix(self, cpsItems, matrix):
        print '\t--- ', ' '.join(map(lambda x: x[0], cpsItems))
        for x in range(0, len(cpsItems)):
            _matrix = matrix[x].tolist()[0] if hasattr(matrix[x], 'tolist') else matrix[x]
            print '\t', cpsItems[x][0] + "  ", " | ".join(map(lambda y: str(y), _matrix))

    def func_chains(self, tosca, cpsItems):
        forwarding_paths = filter(lambda x: x.type == "tosca.nodes.nfv.FP", tosca.nodetemplates)
        forwarding_paths = map(lambda x: {
            "relations": map(lambda y: y["forwarder"], x.requirements),
            "name": x.name
        }, forwarding_paths)
        
        matrixList = []
        for fp in forwarding_paths:
            matrix = []
            total_cps = len(cpsItems)
            for cp in cpsItems:
                matrix.append([0] * total_cps)
            cps_in_FP = {}
            for forwarder in fp["relations"]:
                fromCP = forwarder["capability"]
                toCP = forwarder['relationship']
                cps_in_FP[fromCP] = 1
                cps_in_FP[toCP] = 1
                # print fromCP, "->", toCP
                names = map(lambda x: x[0], cpsItems)
                fromIndex = names.index(fromCP)
                toIndex = names.index(toCP)
                matrix[fromIndex][toIndex] = 1
            matrixList.append({
                "name": fp["name"],
                "matrix": matrix,
                "total_cps": len(cps_in_FP.items()),
                "cps": cps_in_FP.items()
            })
        return matrixList

    def hasLoop(self, matrix):
        return len(filter(lambda x: x is not 0, matrix.diagonal().tolist()[0])) > 0

    def getPosOfNegative(self, cpsItems, matrix):
        _matrix = matrix.tolist()
        names = map(lambda x: x[0], cpsItems)
        str = "  |> Found connexion problem"
        for x in range(0, len(_matrix)):
            for y in range(0, len(_matrix)):
                if _matrix[x][y] == -1:
                    str += "\n    • " + names[x] + " -x-> " + names[y]
        return str

    def nodesInvolved(self, cpsItems, matrix):
        _matrix = matrix.tolist()
        _names = []
        names = map(lambda x: x[0], cpsItems)
        for x in range(0, len(_matrix)):
            if _matrix[x][x] is not 0:
                _names.append(names[x])
        return _names


    def findLoop(self, connectivity, cpsItems, obj, args):
        matrix = obj['matrix']
        total_cps = obj['total_cps']
        name = obj['name']
        m = np.matrix(matrix)
        n = total_cps
        if args.verbose or args.diff:
            pyfancy("\n   -->  ").underlined(name +":").output()
            self.printMatrix(cpsItems, m)
        difference = np.matrix(connectivity) - m
        bugs = []
        if args.diff:
            if difference.min() == -1:
                pyfancy().yellow("\n\tConnexion problem detected").output()
            else:
                pyfancy().dim("diff->").output()
            self.printMatrix(cpsItems, difference)
        if difference.min() == -1:
            bugs.append(self.getPosOfNegative(cpsItems, difference))
        for x in range(1, n + 1):
            matrixToPower = m**x
            if (self.hasLoop(matrixToPower)):
                cpsInvolved = ", ".join(self.nodesInvolved(cpsItems, matrixToPower))
                bugs.append("  |> Found loop!\n    • Length: " + str(x) + "\n    •    CPs: " + cpsInvolved)
                if args.verbose:
                    pyfancy().yellow("\n\tLoop detected in the matrix below: ^("+str(x)+")").output()
                    self.printMatrix(cpsItems, matrixToPower)
                break
        if not args.verbose and not args.diff:
            if len(bugs) is not 0:
                pyfancy().underlined("⚠️  " + name).output()
                for bug in bugs:
                    print bug
            else:
                pyfancy("✅  " + name).output()
        # print ""

    def parse(self, path, args, a_file=True):
        # print("")
        output = None
        tosca = None
        try:
            tosca = ToscaTemplate(path, None, a_file)
        except:
            print("⚠️ tosca-parser: Could not parse the given file.")
            if args.verbose:
                print("Unexpected error: " + str(sys.exc_info()[1]) + "\n")
            exit(1)

        result = self.connectivityGraph(tosca)
        cpsItems = result['cpsItems']
        connectivity = result['connectivity']
        if args.verbose or args.diff:
            print "\nconnectivity:\n"
            self.printMatrix(cpsItems, connectivity)

        if args.verbose or args.diff:
            print "\nNFS:"
        matrixList = self.func_chains(tosca, result['cpsItems'])
        map(lambda x: self.findLoop(connectivity, cpsItems, x, args), matrixList)
        # print("")


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    ParserShell().main(args)


if __name__ == '__main__':
    main()
