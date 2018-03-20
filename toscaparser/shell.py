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
        parser.add_argument('-c', '--template-file',
                            metavar='<filename>',
                            help=_('YAML template or CSAR file to parse.'))

        return parser
    def logger(self, text):
        if (True):
            print(text)
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
                self.parse(path)
            except TOSCAException as err:
                print("\nCould not parse yaml field.")
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print(err)
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        elif toscaparser.utils.urlutils.UrlUtils.validate_url(path):
            self.parse(path, False)
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
            print '\t', cpsItems[x][0], matrix[x]
        

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
        return len(filter(lambda x: x==1 , matrix.diagonal().tolist()[0])) > 0

    def findLoop(self, cpsItems, obj):
        matrix = obj['matrix']
        total_cps = obj['total_cps']
        name = obj['name']
        m = np.matrix(matrix)
        n = total_cps
        print "\n\t~~~~~~~~~ "+ name +" ~~~~~~"
        self.printMatrix(cpsItems, m)
        for x in range(1, n + 1):
            if (self.hasLoop(m**x)):
                print "⚠️ Found loop (^"+str(x)+")"
                self.printMatrix(cpsItems, m**x)
                break

    def parse(self, path, a_file=True):
        output = None
        tosca = ToscaTemplate(path, None, a_file)
        
        print "\nconnectivity:\n"
        result = self.connectivityGraph(tosca)
        cpsItems = result['cpsItems']
        self.printMatrix(cpsItems, result['connectivity'])
        
        print "\nrelations:"
        matrixList = self.func_chains(tosca, result['cpsItems'])
        map(lambda x: self.findLoop(cpsItems, x), matrixList)
            

        # version = tosca.version
        # self.logger("\nDetails\n")
        # if tosca.version:
        #     self.logger("      version: " + version)

        # if hasattr(tosca, 'description'):
        #     description = tosca.description
        #     if description:
        #         self.logger("  description: " + description)

        # if hasattr(tosca, 'inputs'):
        #     inputs = tosca.inputs
        #     if inputs:
        #         self.logger("\ninputs:")
        #         for input in inputs:
        #             self.logger("\t" + input.name)

        # if hasattr(tosca, 'nodetemplates'):
        #     nodetemplates = tosca.nodetemplates
        #     if nodetemplates:
        #         self.logger("nodetemplates:")
        #         networks = []
        #         vnfs = []
        #         for node in nodetemplates:
        #             self.logger("  - name: " + node.name)
        #             self.logger("  - type: " + node.type)
        #             if (node.type == "tosca.nodes.network.Network"):
        #                 network = { "node": node }
        #                 if node._properties:
        #                     for prop in node._properties:
        #                         if (prop.name == 'network_name'):
        #                             network['network_name'] = prop.value
        #                 networks.append(network)
        #             elif (node.type == "tosca.groups.nfv.VNFFG"):
        #                 vnf = {}
        #                 if node._properties:
        #                     for prop in node._properties:
        #                         vnf[prop.name] = prop.value
        #                 vnfs.append(vnf)
        #             self.logger("  - capabilities: ")
        #             for capa in node.get_capabilities_objects():
        #                 self.logger("    * " + capa.name + ":")
        #                 self.logger("      - props: " + str(capa._properties))
        #         print("\nFound (", len(vnfs), ") VNFs!")
        #         for vnf in vnfs:
        #             print(" -", vnf)
        #         print("\nFound (", len(networks), ") networks!")
        #         for network in networks:
        #             print(" -", network.get('network_name'))


        # example of retrieving policy object
        '''if hasattr(tosca, 'policies'):
            policies = tosca.policies
            if policies:
                print("policies:")
                for policy in policies:
                    print("\t" + policy.name)
                    if policy.triggers:
                        print("\ttriggers:")
                        for trigger in policy.triggers:
                            print("\ttrigger name:" + trigger.name)'''

        # if hasattr(tosca, 'outputs'):
        #     outputs = tosca.outputs
        #     if outputs:
        #         print("\n\noutputs:")
        #         for output in outputs:
        #             print("\t" + output.name)
        print("\n")


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    ParserShell().main(args)


if __name__ == '__main__':
    main()
