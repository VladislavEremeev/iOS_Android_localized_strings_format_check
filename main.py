# -*- coding:utf-8 -*-

from os import walk, path, makedirs
from optparse import OptionParser
from re import match, findall
from codecs import open
from lxml import etree


def options_parser():
    parser = OptionParser()

    parser.add_option("-o", "--operation_system",
                      type="string",
                      default="multiple",
                      help="Choose ios or android",
                      metavar="operation_system")

    parser.add_option("-p", "--path",
                      help=".lproj/ (ios) or values/ (android) dirs root",
                      metavar="path")

    (options, _) = parser.parse_args()

    if options.operation_system != 'ios' and  options.operation_system != 'android':
        raise Exception('Invalid OS! Choose from -o android or -o ios')
    if options.path == '':
        raise Exception('Invalid path! Path must be at least 1 symbol')

    return options


class StringsFileUtil:
    """iOS Localizable.strings file util"""

    @staticmethod
    def writeToFile(keys, values, directory, name, additional):
        if not path.exists(directory):
            makedirs(directory)
        fo = open(directory + "/" + name, "wb")
        for x in range(len(keys)):
            if values[x] is None or values[x] == '':
                continue

            key = keys[x].strip()
            value = values[x]
            content = "\"" + key + "\" " + "= " + "\"" + value + "\";\n"
            fo.write(content)
        if additional is not None:
            fo.write(additional)
        fo.close()

    @staticmethod
    def getKeysAndValues(path):
        if path is None:
            return

        # 1.Read localizable.strings
        encodings = ['utf-8', 'utf-16']
        for e in encodings:
            try:
                file = open(path, 'r', encoding=e)
                string = file.read()
                file.close()
            except UnicodeDecodeError:
                print('got unicode error with %s , trying different encoding' % e)
            else:
                break

        # 2.Remove comments
        for x in findall(r'("[^\n]*"(?!\\))|(//[^\n]*$|/(?!\\)\*[\s\S]*?\*(?!\\)/)', string, 8):
            string = string.replace(x[1], '')

        # 3.Split by ";
        localStringList = string.split('\";')
        list = [x.split(' = ') for x in localStringList]

        # 4.Get keys & values
        keys = []
        values = []
        for x in range(len(list)):
            keyValue = list[x]
            if len(keyValue) > 1:
                key = keyValue[0].split('\"')[1]
                value = keyValue[1][1:]
                keys.append(key)
                values.append(value)

        return (keys, values)


def parse_ios_strings_into_dict(path):
    strings = {}
    for _, dir_names, _ in walk(path):
        lproj_dirs = [di for di in dir_names if di.endswith(".lproj")]
        for dirname in lproj_dirs:
            for _, _, filenames in walk(path+'/'+dirname):
                strings_files = [fi for fi in filenames if fi.endswith(".strings")]
                for stringfile in strings_files:
                    child_dict = {}
                    path1 = path+'/' + dirname + '/' + stringfile
                    (keys, values) = StringsFileUtil.getKeysAndValues(path1)
                    for i in range(len(keys)):
                        value = values[i]
                        key = keys[i]
                        if key[-4:] == '.iOS':
                            child_dict[key] = value
                    if path1 in strings:
                        strings[path1] += child_dict
                    else:
                        strings[path1] = child_dict
    if strings == {}:
        raise Exception('Nothing was finded! Are files empty?')
    return strings


def parse_android_strings_into_dict(path):
    strings = {}
    for _, dir_names, _ in walk(path):
        values_dirs = [di for di in dir_names if di.startswith("values")]
        for dirname in values_dirs:
            for _, _, filenames in walk(path+'/'+dirname):
                strings_files = [fi for fi in filenames if fi == "strings.xml"]
                for stringfile in strings_files:
                    child_dict = {}
                    path1 = path+'/' + dirname + '/' + stringfile
                    path1 = path1.replace("//","/")
                    path1 = path1.replace("\\"[:1],"/")

                    parser = etree.XMLParser(remove_comments=True, strip_cdata=False)
                    tree = etree.parse(path1, parser=parser)
                    root = tree.getroot()
                    for element in root.iter():
                        if "name" in element.attrib:
                            if ".android" in element.attrib["name"]:
                                if b"CDATA" in etree.tostring(element):
                                    child_dict[element.attrib["name"]] = str(etree.tostring(element))
                                else:
                                    child_dict[element.attrib["name"]] = element.text
                    strings[path1] = child_dict
    if strings == {}:
        raise Exception('Nothing was finded!')
    return strings


def clean_ios_strings(strings):
    checked_symbol = ':'
    cleaned_strings = {}
    for path in strings:
        child_cleared_dict = {}
        for key, value in strings[path].items():
            cleared_values = []
            temp_string = ''
            if checked_symbol in value:
                iterator = 0
                for symbol in value:
                    iterator +=1
                    if symbol == checked_symbol:
                        if len(temp_string) > 1:
                            cleared_values += [temp_string]
                            temp_string = ':'
                            continue
                        else:
                            temp_string = ':'
                            continue
                    if symbol != checked_symbol and len(temp_string) > 0 and symbol.isalpha():
                        if match('[A-aZ-z]',symbol):
                            temp_string += symbol
                            continue
                    if symbol != checked_symbol and len(temp_string) > 1 and not symbol.isalpha():
                        cleared_values += [temp_string]
                        temp_string = ''
                        continue
                    if iterator == len(value) and len(temp_string) > 1:
                        cleared_values += [temp_string]
                        continue
                    if temp_string != '' and temp_string != ':':
                        cleared_values += [temp_string]
                        temp_string = ''
                    temp_string = ''
            if len(temp_string) > 1:
                cleared_values += [temp_string]
            if key in child_cleared_dict:
                child_cleared_dict[key] += cleared_values
            else:
                child_cleared_dict[key] = cleared_values
        cleaned_strings[path] = child_cleared_dict
    return cleaned_strings


def clean_android_strings(strings):
    cleaned_strings = {}
    child_cleared_dict = {}
    for path in strings:
        child_cleared_dict = {}
        for key in strings[path]:
            value = strings[path][key]
            quantity = 0
            temp1 = []
            if 'CDATA' in value:
                if '<![CDATA[' in value and ']]>' in value:
                    value = value.replace("<![CDATA[","")
                    value = value.replace("]]>", "")
                    temp = findall('<[^>]*>', value)
                    for i in range(0,len(temp)):
                        if not findall("(string)", temp[i]):
                            temp1.append(temp[i])
                    child_cleared_dict[key] = temp1
            else:
                temp = value.split()
                for word in temp:
                    # %1$d | %2$.2f |  %.1d | %s
                    temp_array = findall('(%[0-9]+\$[sdf])|(%[0-9]+\$\.[0-9][sdf])|(%\.[0-9][sdf])|(\%[sd])', word)
                    if temp_array != []:
                        quantity += len(temp_array)
                if quantity != 0:
                    child_cleared_dict[key] = quantity
        cleaned_strings[path] = child_cleared_dict
    return cleaned_strings


def validate_ios_strings(cleaned_strings, strings):
    template = {}
    for path in cleaned_strings:
        if 'en.lproj' in path:
            template = cleaned_strings.pop(path)
            original_en_dict = strings[path]
            break

    for path in cleaned_strings:
        original_all_dict = strings[path]
        child_dict = cleaned_strings[path]
        for key in child_dict:
            equals = 0
            values_array_in_child_dict = child_dict[key]
            values_array_in_template = template[key]
            if len(values_array_in_child_dict) != len(values_array_in_template):
                print('path =', path, ';', 'key=', key, '||||| Испорченный ключ!')
                print('Эталонная строка =', original_en_dict[key], '\n',
                      'Переведённая строка =', original_all_dict[key])
                print('Ожидаемый результат:', values_array_in_template, ';',
                      'Фактический = ', values_array_in_child_dict, '\n')
            else:
                for i in range(0, len(values_array_in_template)):
                    for j in range(0, len(values_array_in_child_dict)):
                        if values_array_in_template[i] in values_array_in_child_dict[j]:
                            equals +=1
                if equals != len(values_array_in_template):
                    print('path =', path, ';', 'key=', key, '||||| Испорченный ключ!')
                    print('Эталонная строка =', original_en_dict[key], '\n',
                          'Переведённая строка =', original_all_dict[key])
                    print('Ожидаемый результат:', values_array_in_template, ';',
                          'Фактический = ', values_array_in_child_dict, '\n')

            #if child_dict[key] != template[key]:  для сравнения по key:[values..]


def validate_android_strings(cleaned_strings):
    template = {}
    for path in cleaned_strings:
        if '/values/' in path:
            template = cleaned_strings.pop(path)
            original_en_dict = strings[path]
            break

    for path in cleaned_strings:
        original_all_dict = strings[path]
        child_dict = cleaned_strings[path]
        for key in template:
            if key not in child_dict:
                print('This key is missing in the translation!')
                print('path =', path)
                print('key=', key, '\n')
                break
            elif isinstance(template[key], int):
                if child_dict[key] != template[key]:
                    print('Wrong number of resource arguments in string!')
                    print('path =', path)
                    print('key=', key)
                    print('Expected result:', template[key], ';', '\n', 'Actual = ', child_dict[key], '\n')
            else:
                if len(child_dict[key]) != len(template[key]):
                    print('Wrong number of tags in CDATA!')
                    print('path =', path)
                    print('key=', key)
                    print('Expected result:', template[key], ';', '\n', 'Actual = ', child_dict[key], '\n')


options = options_parser()
if options.operation_system == 'ios':
    strings = parse_ios_strings_into_dict(options.path)
    cleaned_strings = clean_ios_strings(strings)
    validate_ios_strings(cleaned_strings, strings)
elif options.operation_system == 'android':
    strings = parse_android_strings_into_dict(options.path)
    cleaned_strings = clean_android_strings(strings)
    validate_android_strings(cleaned_strings)
