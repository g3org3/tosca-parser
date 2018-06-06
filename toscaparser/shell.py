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
from toscaparser.utils.gettextutils import _
import toscaparser.utils.urlutils

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
                            help=_('YAML template or CSAR file to parse. [🐯 ]'))

        return parser

    def printIfHasProp(self, tosca, prop):
        if hasattr(tosca, prop):
            value = tosca[prop]
            if value:
                print("\n" + prop + ":")
                print(value)

    def main(self, argv):
        parser = self.get_parser(argv)
        (args, extra_args) = parser.parse_known_args(argv)
        path = args.template_file
        if (args.version):
            print "v1.0.0"
            exit(0)
        if (not args.template_file):
            if (os.path.isfile('./tosca-conf.yml')):
                path = './tosca-conf.yml'
            else:
                print "\n🤔 Could not found default config file: `./tosca-conf.yml`"
                print ""
                print "  to provide explicitly the path please use `-c`"
                print "  e.g. tosca-parser -c ./my-template.yaml"
                print ""
                print "  to display default help use `--help`"
                print ""
                exit(1)
        if os.path.isfile(path):
            self.parse(path)
        elif toscaparser.utils.urlutils.UrlUtils.validate_url(path):
            self.parse(path, False)
        else:
            raise ValueError(_('"%(path)s" is not a valid file.')
                            % {'path': path})

    def parse(self, path, a_file=True):
        output = None
        tosca = ToscaTemplate(path, None, a_file)

        version = tosca.version
        if tosca.version:
            print("\nversion: " + version)

        if hasattr(tosca, 'description'):
            description = tosca.description
            if description:
                print("\ndescription: " + description)

        if hasattr(tosca, 'inputs'):
            inputs = tosca.inputs
            if inputs:
                print("\ninputs:")
                for input in inputs:
                    print("\t" + input.name)

        if hasattr(tosca, 'nodetemplates'):
            nodetemplates = tosca.nodetemplates
            if nodetemplates:
                print("\nnodetemplates:")
                for node in nodetemplates:
                    print("\t" + node.name)

        # self.printIfHasProp(tosca, 'topology_template')

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

        if hasattr(tosca, 'outputs'):
            outputs = tosca.outputs
            if outputs:
                print("\noutputs:")
                for output in outputs:
                    print("\t" + output.name)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    ParserShell().main(args)


if __name__ == '__main__':
    main()
