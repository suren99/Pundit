__author__ = "Surendran Kanagraj"
__email__ = "surend35@gmail.com"
__maintainers__ = "surend35@gmail.com"

import sys
import os
import subprocess
import re

class ctags:
        def __init__(self, name):
            self.file = name

        def __get_ctags_out(self, option):
                return subprocess.check_output("ctags -x --c-kinds={} {} --sort=no".format(option, self.file), shell=True)

        def __get_enum(self):
                return self.__get_ctags_out("g")

        def __get_enum_members(self):
                return self.__get_ctags_out("e")

        def __get_struct(self):
                return self.__get_ctags_out("s")

        def __get_union(self):
                return self.__get_ctags_out("u")

        def __get_struct_union_members(self):
                return self.__get_ctags_out("m")

        def __get_functions(self):
                return self.__get_ctags_out("fp")

        '''
                fp_prot is of the following format
                return_type func_name(arg1, .....)

                We are interested in filtering out arg1.... argn
        '''
        def __get_args_list(self, fp_prot, function_name):
                args_start = fp_prot.find(function_name)
                # starts with open bracket
                nr_bracs = 1
                string_till_now = ""

                # search starts from this index
                idx = args_start + len(function_name) + 1

                args_list = []

                while idx < len(fp_prot) - 1:
                        # this is the only condition which indicates the end of an arg
                        if fp_prot[idx] == ',' and nr_bracs == 1:
                                # current argument is string_till_now
                                args_list.append(string_till_now)
                                string_till_now = ""
                                idx += 1
                                continue

                        if fp_prot[idx] == '(':
                                nr_bracs += 1

                        if fp_prot[idx] == ')':
                                nr_bracs -=1

                        string_till_now += fp_prot[idx]
                        idx += 1

                # Append the last argument which was missed
                if string_till_now.strip() != "":
                        args_list.append(string_till_now)

                # lets ctags help us in filtering out types
                with open("__cg_temp.c", "w") as fp:
                        txt = "struct temp {\n" + ",\n".join(args_list) + ",\n};"
                        fp.write(txt)
                ctags_obj = ctags("__cg_temp.c")
                filtered_args = [each[2] for each in ctags_obj.get_struct_and_union_members()]
                os.system("rm __cg_temp.c")

                return filtered_args

        '''
                resolves ctags output string ---to----> [line no, type, name, misc]
        '''
        def __resolve(self, string):
                res = []
                # string has all the target_types found separated by newline
                for each in [each for each in string.split("\n") if each]:
                        # each target_type info is separated by space
                        words = [s.strip() for s in each.split(' ') if s]
                        # words[4:] holds function prototype which we care
                        target_name, target_type, target_line_no, misc = words[0], words[1], words[2], ' '.join(words[4:])
                        if target_type == "function":
                                args = self.__get_args_list(misc, target_name)
                                res.append([int(target_line_no), target_type, target_name, args])
                        else:
                                res.append([int(target_line_no), target_type, target_name])
                return res

        def get_function_names_and_args(self):
                return self.__resolve(self.__get_functions())

        def get_struct(self):
                return self.__resolve(self.__get_struct())

        def get_enum(self):
                return self.__resolve(self.__get_enum())

        def get_union(self):
                return self.__resolve(self.__get_union())

        def get_enum_members(self):
                return self.__resolve(self.__get_enum_members())

        def get_struct_and_union_members(self):
                return self.__resolve(self.__get_struct_union_members())

class comment:
        def __init__(self, line_no, _type, name, child_list):
                self.line_no = line_no
                self.type = _type
                self.header = name
                self.header_desc = "\n"
                self.child_list = child_list
                self.child_desc = ["\n"] * len(child_list)
                self.context_desc = "\n"
                self.return_desc = "\n"
                self.comment_desc = "\n"

        def populate_by_dissolve(self, comment, type):
                lines = comment.split("\n")

                # not a comment format
                if lines[0][:3] != "/**" or lines[len(lines) - 2][:3] != " */":
                        return False

                self.type = type
                res = [True]

                # Get the args and its desc
                children = re.findall("\* (?=@(.+):([\s\S]+?) \*(?: @|\n))+", comment)
                for child, data in children:
                        self.child_list.append(child)
                        self.child_desc.append(data)

                # Get the comment header and description
                header = re.findall("\* (?=(.+) -([\s\S]+?) \*(?: @|\n))+", comment)
                if len(header):
                        self.header, self.header_desc = header[0]
                else: #wrong format?
                        res[0] = False
                        res.append("header")

                # Get the comment description
                description = re.findall("\* .+ -[\s\S]+? \*\n \*([\s\S]+?)(?: \*\n \* Context)", comment)
              #  print "description : ", description, comment
                if len(description):
                        self.comment_desc = description[0]
                else: # wrong format?
                        res[0] = False
                        res.append("comment description")

                if self.type == "function":
                        # Get the context info
                        context = re.findall("Context:([\s\S]+?) \*(?: \n| Return)", comment)
                        if len(context):
                                self.context_desc = context[0]
                        else: # wrong format ?
                                res[0] = False
                                res.append("Context description")

                        # Get the return data
                        returns = re.findall("Return:([\s\S]+?) \*/", comment)
                        if len(returns):
                                self.return_desc = returns[0]
                        else: # wrong format?
                                res[0] = False
                                res.append("Return description")
                return res

        def form_comment(self):
                # comment start
                comment = "/**\n"
                comment += " * "
                comment += self.header
                if self.type == "function":
                        comment += "()"
                comment += " -"+ self.header_desc

                # args now
                for i in range(len(self.child_list)):
                        comment += " * @"+self.child_list[i]+":"+self.child_desc[i]

                # Description if any
                comment += " *\n *" + self.comment_desc

                if self.type == "function":
                        comment += " *\n"
                        # Context any ?
                        comment += " * Context:"+self.context_desc
                        # Return if function"
                        comment += " * Return:" + self.return_desc

                # comment end
                comment += " */\n"

                return comment

        def compare_child_list(self, to_compare):
                if self.child_list == to_compare:
                        return True
                return False

        def update(self, x):
                self.update_type(x)
                self.update_child_list(x)
                self.update_name(x)
                self.update_return_desc(x)
                self.update_desc(x)
                self.update_context(x)

        def update_type(self, x):
                self.type = x.type

        def update_desc(self, x):
                self.comment_desc = x.comment_desc

        def update_context(self, x):
                self.context_desc = x.context_desc

        def update_name(self, x):
                self.header_desc = x.header_desc

        def update_return_desc(self, x):
                self.return_desc = x.return_desc

        def update_child_list(self, to_compare):
                #assign child data if already available
                for i in range(len(to_compare.child_list)):
                        try:
                                index = self.child_list.index(to_compare.child_list[i])
                                self.child_desc[index] = to_compare.child_desc[i]
                        except ValueError:
                                pass

def find_comment(lines, line_no):
        # comment always ends in the previous line of the target
        comment_end = line_no - 2
        comment_start = comment_end
        asteriks = 0
        while comment_start >= 0:
                if lines[comment_start][:3] == "/**":
                        break
                if lines[comment_start][:2] == " *":
                        asteriks += 1
                comment_start -= 1

        if comment_start < 0:
                return []

        # Comment is proper and valid ?
        if (comment_end - comment_start) != asteriks:
                return []

        return [comment_start, comment_end]

def get_target_end_line(start_line, file_path):
        return int(subprocess.check_output("awk -v s="+ str(start_line) +" 'NR>=s && /{/{c++} NR>=s && /}/ && c && !--c {print NR; exit}' "+file_path, shell=True))

def ctags_out_to_comments(a, file_path):
        comments = {}
        i = 0
        parent = []
        members = []
        while i < len(a):
                if a[i][1] in ["function", "struct", "union", "enum"]:
                        if len(parent):
                                if parent[1] == "function":
                                        comment_obj = comment(parent[0], parent[1], parent[2], parent[3])
                                else:
                                        comment_obj = comment(parent[0], parent[1], parent[2], members)
                                comments[parent[0]] = comment_obj
                        parent = a[i]
                        members = []
                else:
                        if len(parent) and (get_target_end_line(parent[0], file_path) > a[i][0]): 
                            members.append(a[i][2])
                i += 1

        if len(parent):
                if parent[1] == "function":
                        comment_obj = comment(parent[0], parent[1], parent[2], parent[3])
                else:
                        comment_obj = comment(parent[0], parent[1], parent[2], members)
                comments[parent[0]] = comment_obj

        return comments

class checker:
        def __init__(self):
            self.WARNING = '\033[93m'
            self.ERROR = '\033[91m'
            self.ENDC = '\033[0m'
            self.warning_count = 0
            self.error_count = 0

        def issue_warn(self, string):
                self.warning_count += 1
                return self.WARNING + "WARNING: " + self.ENDC + string + "\n"

        def issue_err(self, string):
                self.error_count += 1
                return self.ERROR + "ERROR: " + self.ENDC + string + "\n"

        def compare_and_display(self, comment_in_file, comment_to_be):
                to_print = ""
                if comment_in_file.header.replace("()","") != comment_to_be.header:
                        to_print += self.issue_err("Missing or incorrect header name '{}' found: {}".format(comment_to_be.header, comment_in_file.header))

                if comment_in_file.header.replace(" ","") == "\n":
                        to_print += self.issue_err("Missing header description")

                for i in range(len(comment_to_be.child_list)):
                        if len(comment_in_file.child_list) == i:
                            to_print += self.issue_err("Missing one or more members: '"+ ','.join(comment_to_be.child_list[i:]) +"'")
                            break

                        if comment_to_be.child_list[i] != comment_in_file.child_list[i]:
                                to_print += self.issue_err("Missing or Incorrect placement of member '{}' found: '{}'".format(comment_to_be.child_list[i], comment_in_file.child_list[i]))
                        elif len(comment_in_file.child_list) > i and comment_in_file.child_desc[i].replace(" ", "") == "\n":
                                to_print += self.issue_err("Missing description for member '{}'".format(comment_to_be.child_list[i]))

                if comment_in_file.comment_desc.replace(" ","") == "\n":
                        to_print += self.issue_warn("No description found for the target")

                if comment_in_file.context_desc.replace(" ","") == "\n":
                        if comment_in_file.type == "function":
                                to_print += self.issue_warn("Missing description for 'Context'")
                elif comment_in_file.type != "function":
                        to_print += self.issue_err("Description for Context found for target which is not function")

                if comment_in_file.return_desc.replace(" ","") == "\n":
                        if comment_in_file.type == "function":
                                to_print += self.issue_err("Missing description for 'Return'")
                elif comment_in_file.type != "function":
                        to_print += self.issue_err("Description for Return found for target which is not function")

                if to_print:
                        print "Found errors or warnings for target '{}' at line:{}".format(comment_to_be.header, comment_to_be.line_no)
                        print to_print

if __name__ == '__main__':
        if len(sys.argv) < 3:
            print "Usage python comment_gen.py [--fix | --check] <file_name> -o <output_file>"

        opt = sys.argv[1]
        if opt in ["--fix", "-f", "-F"]:
                opt = "--fix"
        elif opt in ["--check", "-ch", "-c"]:
                opt  = "-c"
        else:
            print "Wrong argument passed"
            sys.exit(1)
        file_path = sys.argv[2]
       
        with open(file_path, "r") as fp:
                lines = fp.readlines()

        ctags_obj = ctags(file_path)
        checker_obj = checker()

        # Collect all info from file.
        res = ctags_obj.get_function_names_and_args()
        res += ctags_obj.get_struct()
        res += ctags_obj.get_union()
        res += ctags_obj.get_enum()
        res += ctags_obj.get_struct_and_union_members()
        res += ctags_obj.get_enum_members()

        # sort based on line numbers
        res.sort(key=lambda el: el[0])

        comments_to_be = ctags_out_to_comments(res, file_path)

        to_write = ""
        filename, file_extension = os.path.splitext(file_path)
        write_done = 0
        for line_no, comment_obj in sorted(comments_to_be.iteritems()):
                comment_present = find_comment(lines, line_no)
                # Comment is already present, Try to retrieve info from past comments if any
                if len(comment_present):
                        old_comment = ''.join(lines[comment_present[0]: comment_present[1] + 1])
                        old_comment_obj = comment(line_no, 0, 0, [])
                        res = old_comment_obj.populate_by_dissolve(old_comment, comment_obj.type)
                        if opt == "-c" and res[0] == False:
                            print checker_obj.issue_err('Improper comment format({}) for the target "{}" at line:{}.'.format(','.join(res[1:]), comment_obj.header, line_no))
                        elif opt == "-c":
                                checker_obj.compare_and_display(old_comment_obj, comment_obj)
                        else:
                                comment_obj.update(old_comment_obj)
                                to_write += ''.join(lines[write_done: comment_present[0]])
                                to_write += comment_obj.form_comment()
                                write_done = line_no - 1
                else:
                        if opt == "-c":
                                print checker_obj.issue_err('No proper comment found for the target "{}" at line:{}.'.format(comment_obj.header, comment_obj.line_no))
                        else:
                                to_write += ''.join(lines[write_done: line_no - 1])
                                to_write += comment_obj.form_comment()
                                write_done = line_no - 1
        to_write += ''.join(lines[write_done: len(lines)])
        if opt == "-c":
            print "total: {} errors, {} warnings\n".format(checker_obj.error_count, checker_obj.warning_count)
        else:
            op = filename + "_cgmodified" + file_extension
            print "Output file: "+ op
            fp = open(op, "w")
            fp.write(to_write)
            fp.close()
        print "Based on https://www.kernel.org/doc/html/latest/doc-guide/kernel-doc.html."
        print "NOTE: In case of false positives or errors, please feel free to raise a pull request"


