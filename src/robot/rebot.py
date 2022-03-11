#!/usr/bin/env python

#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Module implementing the command line entry point for post-processing outputs.

This module can be executed from the command line using the following
approaches::

    python -m robot.rebot
    python path/to/robot/rebot.py

Instead of ``python`` it is possible to use also other Python interpreters.
This module is also used by the installed ``rebot`` start-up script.

This module also provides :func:`rebot` and :func:`rebot_cli` functions
that can be used programmatically. Other code is for internal usage.
"""

import sys

# Allows running as a script. __name__ check needed with multiprocessing:
# https://github.com/robotframework/robotframework/issues/1137
if 'robot' not in sys.modules and __name__ == '__main__':
    import pythonpathsetter

from robot.conf import RebotSettings
from robot.errors import DataError
from robot.reporting import ResultWriter
from robot.output import LOGGER
from robot.utils import Application
from robot.run import RobotFramework


USAGE = """Rebot -- Robot Framework report and log generator

Version:  <VERSION>

Usage:  rebot [options] robot_outputs
   or:  python -m robot.rebot [options] robot_outputs
   or:  python path/to/robot/rebot.py [options] robot_outputs

Rebot can be used to generate logs and reports in HTML format. It can also
produce new XML output files which can be further processed with Rebot or
other tools.

The easiest way to execute Rebot is using the `rebot` command created as part
of the normal installation. Alternatively it is possible to execute the
`robot.rebot` module directly using `python -m robot.rebot`, where `python`
can be replaced with any supported Python interpreter. Yet another alternative
is running the `robot/rebot.py` script like `python path/to/robot/rebot.py`.

Inputs to Rebot are XML output files generated by Robot Framework or by earlier
Rebot executions. When more than one input file is given, a new top level test
suite containing suites in the given files is created by default. This allows
combining multiple outputs together to create higher level reports. An
exception is that if --merge is used, results are combined by adding suites
and tests in subsequent outputs into the first suite structure. If same test
is found from multiple outputs, the last one replaces the earlier ones.

For more information about Rebot and other built-in tools, see
http://robotframework.org/robotframework/#built-in-tools. For more details
about Robot Framework in general, go to http://robotframework.org.

Options
=======

    --rpa                 Turn on the generic automation mode. Mainly affects
                          terminology so that "test" is replaced with "task"
                          in logs and reports. By default the mode is got
                          from the processed output files.
 -R --merge               When combining results, merge outputs together
                          instead of putting them under a new top level suite.
                          Example: rebot --merge orig.xml rerun.xml
 -N --name name           Set the name of the top level suite.
 -D --doc documentation   Set the documentation of the top level suite.
                          Simple formatting is supported (e.g. *bold*). If
                          the documentation contains spaces, it must be quoted.
                          If the value is path to an existing file, actual
                          documentation is read from that file.
                          Examples: --doc "Very *good* example"
                                    --doc doc_from_file.txt
 -M --metadata name:value *  Set metadata of the top level suite. Value can
                          contain formatting and be read from a file similarly
                          as --doc. Example: --metadata Version:1.2
 -G --settag tag *        Sets given tag(s) to all tests.
 -t --test name *         Select tests by name or by long name containing also
                          parent suite name like `Parent.Test`. Name is case
                          and space insensitive and it can also be a simple
                          pattern where `*` matches anything, `?` matches any
                          single character, and `[chars]` matches one character
                          in brackets.
    --task name *         Alias to --test. Especially applicable with --rpa.
 -s --suite name *        Select suites by name. When this option is used with
                          --test, --include or --exclude, only tests in
                          matching suites and also matching other filtering
                          criteria are selected. Name can be a simple pattern
                          similarly as with --test and it can contain parent
                          name separated with a dot. For example, `-s X.Y`
                          selects suite `Y` only if its parent is `X`.
 -i --include tag *       Select tests by tag. Similarly as name with --test,
                          tag is case and space insensitive and it is possible
                          to use patterns with `*`, `?` and `[]` as wildcards.
                          Tags and patterns can also be combined together with
                          `AND`, `OR`, and `NOT` operators.
                          Examples: --include foo --include bar*
                                    --include fooANDbar*
 -e --exclude tag *       Specify tests not to be included by tag. They are not
                          selected even if included with --include. Tags are
                          matched using same rules as with --include.
    --processemptysuite   Processes output also if the top level suite is
                          empty. Useful e.g. with --include/--exclude when it
                          is not an error that there are no matches.
                          Use --skiponfailure when starting execution instead.
 -d --outputdir dir       Where to create output files. The default is the
                          directory where Rebot is run from and the given path
                          is considered relative to that unless it is absolute.
 -o --output file         XML output file. Not created unless this option is
                          specified. Given path, similarly as paths given to
                          --log, --report and --xunit, is relative to
                          --outputdir unless given as an absolute path.
 -l --log file            HTML log file. Can be disabled by giving a special
                          name `NONE`. Default: log.html
                          Examples: `--log mylog.html`, `-l none`
 -m --monitorlog file     Writes results in monitor-style log files
 -r --report file         HTML report file. Can be disabled with `NONE`
                          similarly as --log. Default: report.html
 -x --xunit file          xUnit compatible result file. Not created unless this
                          option is specified.
 -T --timestampoutputs    When this option is used, timestamp in a format
                          `YYYYMMDD-hhmmss` is added to all generated output
                          files between their basename and extension. For
                          example `-T -o output.xml -r report.html -l none`
                          creates files like `output-20070503-154410.xml` and
                          `report-20070503-154410.html`.
    --splitlog            Split the log file into smaller pieces that open in
                          browsers transparently.
    --logtitle title      Title for the generated log file. The default title
                          is `<SuiteName> Log`.
    --reporttitle title   Title for the generated report file. The default
                          title is `<SuiteName> Report`.
    --reportbackground colors  Background colors to use in the report file.
                          Given in format `passed:failed:skipped` where the
                          `:skipped` part can be omitted. Both color names and
                          codes work.
                          Examples: --reportbackground green:red:yellow
                                    --reportbackground #00E:#E00
 -L --loglevel level      Threshold for selecting messages. Available levels:
                          TRACE (default), DEBUG, INFO, WARN, NONE (no msgs).
                          Use syntax `LOGLEVEL:DEFAULT` to define the default
                          visible log level in log files.
                          Examples: --loglevel DEBUG
                                    --loglevel DEBUG:INFO
    --suitestatlevel level  How many levels to show in `Statistics by Suite`
                          in log and report. By default all suite levels are
                          shown. Example:  --suitestatlevel 3
    --tagstatinclude tag *  Include only matching tags in `Statistics by Tag`
                          in log and report. By default all tags are shown.
                          Given tag can be a pattern like with --include.
    --tagstatexclude tag *  Exclude matching tags from `Statistics by Tag`.
                          This option can be used with --tagstatinclude
                          similarly as --exclude is used with --include.
    --tagstatcombine tags:name *  Create combined statistics based on tags.
                          These statistics are added into `Statistics by Tag`.
                          If the optional `name` is not given, name of the
                          combined tag is got from the specified tags. Tags are
                          matched using the same rules as with --include.
                          Examples: --tagstatcombine requirement-*
                                    --tagstatcombine tag1ANDtag2:My_name
    --tagdoc pattern:doc *  Add documentation to tags matching the given
                          pattern. Documentation is shown in `Test Details` and
                          also as a tooltip in `Statistics by Tag`. Pattern can
                          use `*`, `?` and `[]` as wildcards like --test.
                          Documentation can contain formatting like --doc.
                          Examples: --tagdoc mytag:Example
                                    --tagdoc "owner-*:Original author"
    --tagstatlink pattern:link:title *  Add external links into `Statistics by
                          Tag`. Pattern can use `*`, `?` and `[]` as wildcards
                          like --test. Characters matching to `*` and `?`
                          wildcards can be used in link and title with syntax
                          %N, where N is index of the match (starting from 1).
                          Examples: --tagstatlink mytag:http://my.domain:Title
                          --tagstatlink "bug-*:http://url/id=%1:Issue Tracker"
    --expandkeywords name:<pattern>|tag:<pattern> *
                          Matching keywords will be automatically expanded in
                          the log file. Matching against keyword name or tags
                          work using same rules as with --removekeywords.
                          Examples: --expandkeywords name:BuiltIn.Log
                                    --expandkeywords tag:expand
    --removekeywords all|passed|for|wuks|name:<pattern>|tag:<pattern> *
                          Remove keyword data from all generated outputs.
                          Keywords containing warnings are not removed except
                          in the `all` mode.
                          all:     remove data from all keywords
                          passed:  remove data only from keywords in passed
                                   test cases and suites
                          for:     remove passed iterations from for loops
                          while:   remove passed iterations from while loops
                          wuks:    remove all but the last failing keyword
                                   inside `BuiltIn.Wait Until Keyword Succeeds`
                          name:<pattern>:  remove data from keywords that match
                                   the given pattern. The pattern is matched
                                   against the full name of the keyword (e.g.
                                   'MyLib.Keyword', 'resource.Second Keyword'),
                                   is case, space, and underscore insensitive,
                                   and may contain `*`, `?` and `[]` wildcards.
                                   Examples: --removekeywords name:Lib.HugeKw
                                             --removekeywords name:myresource.*
                          tag:<pattern>:  remove data from keywords that match
                                   the given pattern. Tags are case and space
                                   insensitive and patterns can contain `*`,
                                   `?` and `[]` wildcards. Tags and patterns
                                   can also be combined together with `AND`,
                                   `OR`, and `NOT` operators.
                                   Examples: --removekeywords foo
                                             --removekeywords fooANDbar*
    --flattenkeywords for|while|iteration|name:<pattern>|tag:<pattern> *
                          Flattens matching keywords in all generated outputs.
                          Matching keywords get all log messages from their
                          child keywords and children are discarded otherwise.
                          for:     flatten FOR loops fully
                          while:   flatten WHILE loops fully
                          iteration: flatten FOR/WHILE loop iterations
                          foritem: deprecated alias for `iteration`
                          name:<pattern>:  flatten matched keywords using same
                                   matching rules as with
                                   `--removekeywords name:<pattern>`
                          tag:<pattern>:  flatten matched keywords using same
                                   matching rules as with
                                   `--removekeywords tag:<pattern>`
    --starttime timestamp  Set execution start time. Timestamp must be given in
                          format `2007-10-01 15:12:42.268` where all separators
                          are optional (e.g. `20071001151242268` is ok too) and
                          parts from milliseconds to hours can be omitted if
                          they are zero (e.g. `2007-10-01`). This can be used
                          to override start time of a single suite or to set
                          start time for a combined suite, which would
                          otherwise be `N/A`.
    --endtime timestamp   Same as --starttime but for end time. If both options
                          are used, elapsed time of the suite is calculated
                          based on them. For combined suites, it is otherwise
                          calculated by adding elapsed times of the combined
                          suites together.
    --nostatusrc          Sets the return code to zero regardless are there
                          failures. Error codes are returned normally.
    --prerebotmodifier class *  Class to programmatically modify the result
                          model before creating outputs.
 -C --consolecolors auto|on|ansi|off  Use colors on console output or not.
                          auto: use colors when output not redirected (default)
                          on:   always use colors
                          ansi: like `on` but use ANSI colors also on Windows
                          off:  disable colors altogether
 -P --pythonpath path *   Additional locations to add to the module search path
                          that is used when importing Python based extensions.
 -A --argumentfile path *  Text file to read more arguments from. File can have
                          both options and output files, one per line. Contents
                          do not need to be escaped but spaces in the beginning
                          and end of lines are removed. Empty lines and lines
                          starting with a hash character (#) are ignored.
                          Example file:
                          |  --include regression
                          |  --name Regression Tests
                          |  # This is a comment line
                          |  output.xml
 -h -? --help             Print usage instructions.
 --version                Print version information.

Options that are marked with an asterisk (*) can be specified multiple times.
For example, `--test first --test third` selects test cases with name `first`
and `third`. If an option accepts a value but is not marked with an asterisk,
the last given value has precedence. For example, `--log A.html --log B.html`
creates log file `B.html`. Options accepting no values can be disabled by
using the same option again with `no` prefix added or dropped. The last option
has precedence regardless of how many times options are used. For example,
`--merge --merge --nomerge --nostatusrc --statusrc` would not activate the
merge mode and would return a normal return code.

Long option format is case-insensitive. For example, --SuiteStatLevel is
equivalent to but easier to read than --suitestatlevel. Long options can
also be shortened as long as they are unique. For example, `--logti Title`
works while `--lo log.html` does not because the former matches only --logtitle
but the latter matches both --log and --logtitle.

Environment Variables
=====================

REBOT_OPTIONS             Space separated list of default options to be placed
                          in front of any explicit options on the command line.
ROBOT_SYSLOG_FILE         Path to a file where Robot Framework writes internal
                          information about processed files. Can be useful when
                          debugging problems. If not set, or set to special
                          value `NONE`, writing to the syslog file is disabled.
ROBOT_SYSLOG_LEVEL        Log level to use when writing to the syslog file.
                          Available levels are the same as for --loglevel
                          command line option and the default is INFO.

Examples
========

# Simple Rebot run that creates log and report with default names.
$ rebot output.xml

# Using options. Note that this is one long command split into multiple lines.
$ rebot --log smoke_log.html --report smoke_report.html --include smoke
        --ReportTitle "Smoke Tests" --ReportBackground green:yellow:red
        --TagStatCombine tag1ANDtag2 path/to/myoutput.xml

# Executing `robot.rebot` module using Python and creating combined outputs.
$ python -m robot.rebot --name Combined outputs/*.xml
"""


class Rebot(RobotFramework):

    def __init__(self):
        Application.__init__(self, USAGE, arg_limits=(1,), env_options='REBOT_OPTIONS',
                             logger=LOGGER)

    def main(self, datasources, **options):
        try:
            settings = RebotSettings(options)
        except:
            LOGGER.register_console_logger(stdout=options.get('stdout'),
                                           stderr=options.get('stderr'))
            raise
        LOGGER.register_console_logger(**settings.console_output_config)
        if settings.pythonpath:
            sys.path = settings.pythonpath + sys.path
        LOGGER.disable_message_cache()
        rc = ResultWriter(*datasources).write_results(settings)
        if rc < 0:
            raise DataError('No outputs created.')
        return rc


def rebot_cli(arguments=None, exit=True):
    """Command line execution entry point for post-processing outputs.

    :param arguments: Command line options and arguments as a list of strings.
        Defaults to ``sys.argv[1:]`` if not given.
    :param exit: If ``True``, call ``sys.exit`` with the return code denoting
        execution status, otherwise just return the rc.

    Entry point used when post-processing outputs from the command line, but
    can also be used by custom scripts. Especially useful if the script itself
    needs to accept same arguments as accepted by Rebot, because the script can
    just pass them forward directly along with the possible default values it
    sets itself.

    Example::

        from robot import rebot_cli

        rebot_cli(['--name', 'Example', '--log', 'NONE', 'o1.xml', 'o2.xml'])

    See also the :func:`rebot` function that allows setting options as keyword
    arguments like ``name="Example"`` and generally has a richer API for
    programmatic Rebot execution.
    """
    if arguments is None:
        arguments = sys.argv[1:]
    return Rebot().execute_cli(arguments, exit=exit)


def rebot(*outputs, **options):
    """Programmatic entry point for post-processing outputs.

    :param outputs: Paths to Robot Framework output files similarly
        as when running the ``rebot`` command on the command line.
    :param options: Options to configure processing outputs. Accepted
        options are mostly same as normal command line options to the ``rebot``
        command. Option names match command line option long names without
        hyphens so that, for example, ``--name`` becomes ``name``.

    The semantics related to passing options are exactly the same as with the
    :func:`~robot.run.run` function. See its documentation for more details.

    Examples::

        from robot import rebot

        rebot('path/to/output.xml')
        with open('stdout.txt', 'w') as stdout:
            rebot('o1.xml', 'o2.xml', name='Example', log=None, stdout=stdout)

    Equivalent command line usage::

        rebot path/to/output.xml
        rebot --name Example --log NONE o1.xml o2.xml > stdout.txt
    """
    return Rebot().execute(*outputs, **options)


if __name__ == '__main__':
    rebot_cli(sys.argv[1:])
