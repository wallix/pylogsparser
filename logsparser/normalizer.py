# -*- python -*-

# pylogsparser - Logs parsers python library
#
# Copyright (C) 2011 Wallix Inc.
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

"""
Here we have everything needed to parse and use XML definition files.

The only class one should ever use here is L{Normalizer}. The rest is
used during the parsing of the definition files that is taken care of
by the Normalizer class.
"""

import re
import csv
import warnings
import math

from lxml.etree import parse, tostring
from datetime import datetime, timedelta # pyflakes:ignore
import urlparse # pyflakes:ignore
import logsparser.extras as extras # pyflakes:ignore

try:
    import GeoIP #pyflakes:ignore
    country_code_by_address = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE).country_code_by_addr
except ImportError, e:
    country_code_by_address =lambda x: None

# the following symbols and modules are allowed for use in callbacks.
SAFE_SYMBOLS = ["list", "dict", "tuple", "set", "long", "float", "object",
                "bool", "callable", "True", "False", "dir",
                "frozenset", "getattr", "hasattr", "abs", "cmp", "complex",
                "divmod", "id", "pow", "round", "slice", "vars",
                "hash", "hex", "int", "isinstance", "issubclass", "len",
                "map", "filter", "max", "min", "oct", "chr", "ord", "range",
                "reduce", "repr", "str", "unicode", "basestring", "type", "zip",
                "xrange", "None", "Exception", "re", "datetime", "math",
                "urlparse", "country_code_by_address", "extras", "timedelta"]

class Tag(object):
    """A tag as defined in a pattern."""
    def __init__(self,
                 name,
                 tagtype,
                 substitute,
                 description = {},
                 callbacks = []):
        """@param name: the tag's name
        @param tagtype: the tag's type name
        @param substitute: the string chain representing the tag in a log pattern
        @param description = a dictionary holding multilingual descriptions of
        the tag
        @param callbacks: a list of eventual callbacks to fire once the tag value
        has been extracted"""
        self.name = name
        self.tagtype = tagtype
        self.substitute = substitute
        self.description = description
        self.callbacks = callbacks

    def get_description(self, language = 'en'):
        """@Return : The tag description"""
        return self.description.get(language, 'N/A')

class TagType(object):
    """A tag type. This defines how to match a given tag."""
    def __init__(self,
                 name,
                 ttype,
                 regexp,
                 description = {},
                 flags = re.UNICODE | re.IGNORECASE):
        """@param name: the tag type's name
        @param ttype: the expected type of the value fetched by the associated regular expression
        @param regexp: the regular expression (as text, not compiled) associated to this type
        @param description: a dictionary holding multilingual descriptions of
        the tag type
        @param flags: flags by which to compile the regular expression"""
        self.name = name
        self.ttype = ttype
        self.regexp = regexp
        self.description = description
        try:
            self.compiled_regexp = re.compile(regexp, flags)
        except:
            raise ValueError, "Invalid regular expression %s" % regexp
            

# import the common tag types
def get_generic_tagTypes(path = 'normalizers/common_tagTypes.xml'):
    """Imports the common tag types.
    
    @return: a dictionary of tag types."""
    generic = {}
    try:
        tagTypes = parse(open(path, 'r')).getroot()
        for tagType in tagTypes:
            tt_name = tagType.get('name')
            tt_type = tagType.get('ttype') or 'basestring'
            tt_desc = {}
            for child in tagType:
                if child.tag == 'description':
                    for desc in child:
                        lang = desc.get('language') or 'en'
                        tt_desc[lang] = child.text
                elif child.tag == 'regexp':
                    tt_regexp = child.text
            generic[tt_name] = TagType(tt_name, tt_type, tt_regexp, tt_desc)
        return generic
    except StandardError, err:
        warnings.warn("Could not load generic tags definition file : %s \
                       - generic tags will not be available." % err)
        return {}

# import the common callbacks
def get_generic_callBacks(path = 'normalizers/common_callBacks.xml'):
    """Imports the common callbacks.

    @return a dictionnary of callbacks."""
    generic = {}
    try:
        callBacks = parse(open(path, 'r')).getroot()
        for callBack in callBacks:
            cb_name = callBack.get('name')
            # cb_desc = {}
            for child in callBack:
                if child.tag == 'code':
                    cb_code = child.text
		# descriptions are not used yet but implemented in xml and dtd files for later use
                # elif child.tag == 'description':
                #     for desc in child:
                #         lang = desc.get('language')
                #         cb_desc[lang] = desc.text
            generic[cb_name] = CallbackFunction(cb_code, cb_name)
        return generic
    except StandardError, err:
        warnings.warn("Could not load generic callbacks definition file : %s \
                       - generic callbacks will not be available." % err)
        return {}

class PatternExample(object):
    """Represents an log sample matching a given pattern. expected_tags is a
    dictionary of tag names -> values that should be obtained after the
    normalization of this sample."""
    def __init__(self,
                 raw_line,
                 expected_tags = {},
                 description = {}):
        self.raw_line = raw_line
        self.expected_tags = expected_tags
        self.description = description
        
    def get_description(self, language = 'en'):
        """@return : An example description"""
        return { 'sample' : self.raw_line,
                 'normalization' : self.expected_tags }

class Pattern(object):
    """A pattern, as defined in a normalizer configuration file."""
    def __init__(self,
                 name,
                 pattern,
                 tags = {},
                 description = '',
                 commonTags = {},
                 examples = [] ):
        self.name = name
        self.pattern = pattern
        self.tags = tags
        self.description = description
        self.examples = examples
        self.commonTags = commonTags
        
    def normalize(self, logline):
        raise NotImplementedError
        
    def test_examples(self):
        raise NotImplementedError
        
    def get_description(self, language = 'en'):
        tags_desc = dict([ (tag.name, tag.get_description(language)) for tag in self.tags.values() ])
        substitutes = dict([ (tag.substitute, tag.name) for tag in self.tags.values() ])
        examples_desc = [ example.get_description(language) for example in self.examples ]
        return { 'pattern' : self.pattern, 
                 'description' : self.description.get(language, "N/A"),
                 'tags' : tags_desc,
                 'substitutes' : substitutes,
                 'commonTags' : self.commonTags,
                 'examples' : examples_desc }

class CSVPattern(object):
    """A pattern that handle CSV case."""
    def __init__(self,
                 name,
                 pattern,
                 separator = ',',
                 quotechar = '"',
                 tags = {},
                 callBacks = [],
                 tagTypes = {},
                 genericTagTypes = {},
                 genericCallBacks = {},
                 description = '',
                 commonTags = {},
                 examples = []):
        """ 
        @param name: the pattern name
        @param pattern: the CSV pattern
        @param separator: the CSV delimiter
        @param quotechar: the CSV quote character
        @param tags: a dict of L{Tag} instance with Tag name as key
        @param callBacks: a list of L{CallbackFunction}
        @param tagTypes: a dict of L{TagType} instance with TagType name as key
        @param genericTagTypes: a dict of L{TagType} instance from common_tags xml definition with TagType name as key
        @param genericCallBacks: a dict of L{CallBacks} instance from common_callbacks xml definition with callback name as key
        @param description: a pattern description
        @param commonTags: a Dict of tags to add to the final normalisation
        @param examples: a list of L{PatternExample}
        """
        self.name = name
        self.pattern = pattern
        self.separator = separator
        self.quotechar = quotechar
        self.tags = tags
        self.callBacks = callBacks
        self.tagTypes = tagTypes
        self.genericTagTypes = genericTagTypes
        self.genericCallBacks = genericCallBacks
        self.description = description
        self.examples = examples
        self.commonTags = commonTags
        _fields = self.pattern.split(self.separator)
        if self.separator != ' ':
            self.fields = [f.strip() for f in _fields]
        else:
            self.fields = _fields
        self.check_count = len(self.fields)

    def postprocess(self, data):
        for tag in self.tags:
            # tagTypes defined in the conf file take precedence on the
            # generic ones. If nothing found either way, fall back to
            # Anything.
            tag_regexp = self.tagTypes.get(self.tags[tag].tagtype,
                               self.genericTagTypes.get(self.tags[tag].tagtype, self.genericTagTypes['Anything'])).regexp
            r = re.compile(tag_regexp)
            field = self.tags[tag].substitute
            if field not in data.keys():
                continue
            if not r.match(data[field]):
                # We found a tag that not matchs the expected regexp
                return None
            else:
                value = data[field]
                del data[field]
                data[tag] = value
                # try to apply callbacks
                # but do not try to apply callbacks if we do not have any value
                if not data[tag]:
                    continue
                callbacks_names = self.tags[tag].callbacks
                for cbname in callbacks_names:
                    try:
                        # get the callback in the definition file, or look it up in the common library if not found
                        callback = [cb for cb in self.callBacks.values() if cb.name == cbname] or\
                                   [cb for cb in self.genericCallBacks.values() if cb.name == cbname]
                        callback = callback[0]
                    except:
                        warnings.warn("Unable to find callback %s for pattern %s" %
                                     (cbname, self.name))
                        continue
                    try:
                        callback(data[tag], data)
                    except Exception, e:
                        raise Exception("Error on callback %s in pattern %s : %s - skipping" %
                                       (cbname,
                                        self.name, e))
        # remove temporary tags
        temp_tags = [t for t in data.keys() if t.startswith('__')]
        for t in temp_tags:
            del data[t]
        empty_tags = [t for t in data.keys() if not data[t]]
        # remove empty tags
        for t in empty_tags:
            del data[t]
        return data

    def normalize(self, logline):
        # Verify logline is a basestring
        if not isinstance(logline, basestring):
            return None
        # Try to retreive some fields with csv reader
        try:
            data = [data for data in csv.reader([logline], delimiter = self.separator, quotechar = self.quotechar)][0]
        except:
            return None
        # Check we have something in data
        if not data:
            return None
        else:
            # Verify csv reader has match the expected number of fields
            if len(data) != self.check_count:
                return None
            # Check expected for for fileds and apply callbacks
            data = self.postprocess(dict(zip(self.fields, data)))
            # Add common tags
            if data:
                data.update(self.commonTags)
        return data
        
    def test_examples(self):
        raise NotImplementedError
        
    def get_description(self, language = 'en'):
        tags_desc = dict([ (tag.name, tag.get_description(language)) for tag in self.tags.values() ])
        substitutes = dict([ (tag.substitute, tag.name) for tag in self.tags.values() ])
        examples_desc = [ example.get_description(language) for example in self.examples ]
        return { 'pattern' : self.pattern, 
                 'description' : self.description.get(language, "N/A"),
                 'tags' : tags_desc,
                 'substitutes' : substitutes,
                 'commonTags' : self.commonTags,
                 'examples' : examples_desc }

class CallbackFunction(object):
    """This class is used to define a callback function from source code present
    in the XML configuration file. The function is defined in a sanitized
    environment (imports are disabled, for instance).
    This class is inspired from this recipe :
    http://code.activestate.com/recipes/550804-create-a-restricted-python-function-from-a-string/
    """
    def __init__(self, function_body = "log['test'] = value",
                 name = 'unknown'):
        
        source = "def __cbfunc__(value,log):\n"
        source += '\t' + '\n\t'.join(function_body.split('\n')) + '\n'
        
        self.__doc__ = "Callback function generated from the following code:\n\n" + source
        byteCode = compile(source, '<string>', 'exec')
        self.name = name
        
        # Setup a standard-compatible python environment
        builtins   = dict()
        globs      = dict()
        locs       = dict()
        builtins["locals"]  = lambda: locs
        builtins["globals"] = lambda: globs
        globs["__builtins__"] = builtins
        globs["__name__"] = "SAFE_ENV"
        globs["__doc__"] = source
        
        if type(__builtins__) is dict:
            bi_dict = __builtins__
        else:
            bi_dict = __builtins__.__dict__
        
        for k in SAFE_SYMBOLS:
            try:
                locs[k] = locals()[k]
                continue
            except KeyError:
                pass
            try:
                globs[k] = globals()[k]
                continue
            except KeyError:
                pass
            try:
                builtins[k] = bi_dict[k]
            except KeyError:
                pass
        
        # set the function in the safe environment
        eval(byteCode, globs, locs)
        self.cbfunction = locs["__cbfunc__"]
    
    def __call__(self, value, log):
        """call the instance as a function to run the callback."""
        # Exceptions are caught higher up in the normalization process.
        self.cbfunction(value, log)
        return log


class Normalizer(object):
    """Log Normalizer, based on an XML definition file."""
    
    def __init__(self, xmlconf, genericTagTypes, genericCallBacks):
        """initializes the normalizer with an lxml ElementTree.

        @param xmlconf: lxml ElementTree normalizer definition
        @param genericTagTypes: path to generic tags definition xml file
        """
        self.text_source = tostring(xmlconf, pretty_print = True)
        self.sys_path = xmlconf.docinfo.URL
        normalizer = xmlconf.getroot()
        self.genericTagTypes = get_generic_tagTypes(genericTagTypes)
        self.genericCallBacks = get_generic_callBacks(genericCallBacks)
        self.description = {}
        self.authors = []
        self.tagTypes = {}
        self.callbacks = {}
        self.prerequisites = {}
        self.patterns = {}
        self.commonTags = {}
        self.finalCallbacks = []
        self.name = normalizer.get('name')
        if not self.name:
            raise ValueError, "The normalizer configuration lacks a name."
        self.version = float(normalizer.get('version')) or 1.0
        self.appliedTo = normalizer.get('appliedTo') or 'raw'
        self.re_flags = ( (normalizer.get('unicode') == "yes" and re.UNICODE ) or 0 ) |\
                        ( (normalizer.get('ignorecase') == "yes" and re.IGNORECASE ) or 0 ) |\
                        ( (normalizer.get('multiline') == "yes" and re.MULTILINE ) or 0 )
        self.matchtype = ( normalizer.get('matchtype') == "search" and "search" ) or 'match'
        try:
            self.taxonomy = normalizer.get('taxonomy')
        except:
            self.taxonomy = None

        for node in normalizer:
            if node.tag == "description":
                for desc in node:
                    self.description[desc.get('language')] = desc.text
            elif node.tag == "authors":
                for author in node:
                    self.authors.append(author.text)
            elif node.tag == "tagTypes":
                for tagType in node:
                    tT_description = {}
                    tT_regexp = ''
                    for child in tagType:
                        if child.tag == 'description':
                            for desc in child:
                                tT_description[desc.get("language")] = desc.text
                        elif child.tag == 'regexp':
                            tT_regexp = child.text
                    self.tagTypes[tagType.get('name')] = TagType(tagType.get('name'),
                                                                 tagType.get('ttype') or "basestring",
                                                                 tT_regexp,
                                                                 tT_description,
                                                                 self.re_flags)
            elif node.tag == 'callbacks':
                for callback in node:
                    self.callbacks[callback.get('name')] = CallbackFunction(callback.text, callback.get('name'))
            elif node.tag == 'prerequisites':
                for prereqTag in node:
                    self.prerequisites[prereqTag.get('name')] = prereqTag.text
            elif node.tag == 'patterns':
                self.__parse_patterns(node)
            elif node.tag == "commonTags":
                for commonTag in node:
                    self.commonTags[commonTag.get('name')] = commonTag.text
            elif node.tag == "finalCallbacks":
                for callback in node:
                    self.finalCallbacks.append(callback.text)
        # precompile regexp 
        self.full_regexp, self.tags_translation, self.tags_to_pattern, whatever = self.get_uncompiled_regexp()
        self.full_regexp = re.compile(self.full_regexp, self.re_flags)
    
    def __parse_patterns(self, node):
        for pattern in node:
            p_name = pattern.get('name')
            p_description = {}
            p_tags = {}
            p_commonTags = {}
            p_examples = []
            p_csv = {}
            for p_node in pattern:
                if p_node.tag == 'description':
                    for desc in p_node:
                        p_description[desc.get('language')] = desc.text
                elif p_node.tag == 'text':
                    p_pattern = p_node.text
                    if 'type' in p_node.attrib:
                        p_type = p_node.get('type')
                        if p_type == 'csv':
                            p_csv = {'type': 'csv'}
                            if 'separator' in p_node.attrib:
                                p_csv['separator'] = p_node.get('separator')
                            if 'quotechar' in p_node.attrib:
                                p_csv['quotechar'] = p_node.get('quotechar')
                elif p_node.tag == 'tags':
                    for tag in p_node:
                        t_cb = []
                        t_description = {}
                        t_name = tag.get('name')
                        t_tagtype = tag.get('tagType')
                        for child in tag:
                            if child.tag == 'description':
                                for desc in child:
                                    t_description[desc.get('language')] = desc.text
                            if child.tag == 'substitute':
                                t_substitute = child.text
                            elif child.tag == 'callbacks':
                                for cb in child:
                                    t_cb.append(cb.text)
                        p_tags[t_name] = Tag(t_name, t_tagtype, t_substitute, t_description, t_cb) 
                elif p_node.tag == "commonTags":
                    for commontag in p_node:
                        p_commonTags[commontag.get('name')] = commontag.text
                elif p_node.tag == 'examples':
                    for example in p_node:
                        e_description = {}
                        e_expectedTags = {}
                        for child in example:
                            if child.tag == 'description':
                                for desc in child:
                                    e_description[desc.get('language')] = desc.text
                            elif child.tag == 'text':
                                e_rawline = child.text
                            elif child.tag == "expectedTags":
                                for etag in child:
                                    e_expectedTags[etag.get('name')] = etag.text
                        p_examples.append(PatternExample(e_rawline, e_expectedTags, e_description))
            if not p_csv:
                self.patterns[p_name] = Pattern(p_name, p_pattern, p_tags, p_description, p_commonTags, p_examples)
            else:
                self.patterns[p_name] = CSVPattern(p_name, p_pattern, p_csv['separator'], p_csv['quotechar'], p_tags,
                                                   self.callbacks, self.tagTypes, self.genericTagTypes, self.genericCallBacks, p_description,
                                                   p_commonTags, p_examples)

    def get_description(self, language = "en"):
        return "%s v. %s" % (self.name, self.version)
    
    def get_long_description(self, language = 'en'):
        patterns_desc = [ pattern.get_description(language) for pattern in self.patterns.values() ]
        return { 'name' : self.name,
                 'version' : self.version,
                 'authors' : self.authors,
                 'description' : self.description.get(language, "N/A"),
                 'patterns' : patterns_desc,
                 'commonTags' : self.commonTags,
                 'taxonomy' : self.taxonomy }

    def get_uncompiled_regexp(self, p = None, increment = 0):
        """returns the uncompiled regular expression associated to pattern named p.
        If p is None, all patterns are stitched together, ready for compilation.
        increment is the starting value to use for the generic tag names in the
        returned regular expression.
        @return: regexp, dictionary of tag names <-> tag codes,
                 dictionary of tags codes <-> pattern the tag came from,
                 new increment value
        """
        patterns = p
        regexps = []
        tags_translations = {}
        tags_to_pattern = {}
        if not patterns:
            # WARNING ! dictionary keys are not necessarily returned in creation order.
            # This is silly, as the pattern order is crucial. So we must enforce that
            # patterns are named in alphabetical order of precedence ...
            patterns = sorted(self.patterns.keys())
        if isinstance(patterns, basestring):
            patterns = [patterns]
        for pattern in patterns:
            if isinstance(self.patterns[pattern], CSVPattern):
                continue
            regexp = self.patterns[pattern].pattern
            for tagname, tag in self.patterns[pattern].tags.items():
                # tagTypes defined in the conf file take precedence on the
                # generic ones. If nothing found either way, fall back to
                # Anything.
                
                tag_regexp = self.tagTypes.get(tag.tagtype, 
                                               self.genericTagTypes.get(tag.tagtype,
                                                                        self.genericTagTypes['Anything'])).regexp
                named_group = '(?P<tag%i>%s)' % (increment, tag_regexp)
                regexp = regexp.replace(tag.substitute, named_group)
                tags_translations['tag%i' % increment] = tagname
                tags_to_pattern['tag%i' % increment] = pattern
                increment += 1
            regexps.append("(?:%s)" % regexp)
        return "|".join(regexps), tags_translations, tags_to_pattern, increment

    def normalize(self, log, do_not_check_prereq = False):
        """normalization in standalone mode.
        @param log: a dictionary or an object providing at least a get() method
        @param do_not_check_prereq: if set to True, the prerequisite tags check
        is skipped (debug purpose only)
        @return: a dictionary with updated tags if normalization was successful."""
        if isinstance(log, basestring) or not hasattr(log, "get"):
            raise ValueError, "the normalizer expects an argument of type Dict"
        # Test prerequisites
        if all( [ re.match(value, log.get(prereq, ''))
                  for prereq, value in self.prerequisites.items() ]) or\
           do_not_check_prereq:
            csv_patterns = [csv_pattern for csv_pattern in self.patterns.values() if isinstance(csv_pattern, CSVPattern)]
            if self.appliedTo in log.keys():
                m = getattr(self.full_regexp, self.matchtype)(log[self.appliedTo])
                if m is not None:
                    m = m.groupdict()
                if m:
                    # this little trick makes the following line not type dependent
                    temp_wl = dict([ (u, log[u]) for u in log.keys() ])
                    for tag in m:
                        if m[tag] is not None:
                            matched_pattern = self.patterns[self.tags_to_pattern[tag]]
                            temp_wl[self.tags_translation[tag]] = m[tag]
                            # apply eventual callbacks
                            for cb in matched_pattern.tags[self.tags_translation[tag]].callbacks:
                                # TODO it could be desirable to make sure the callback
                                # does not try to change important preset values such as
                                # 'raw' and 'uuid'.
                                try:
                                    # if the callback doesn't exist in the normalizer file, it will
                                    # search in the commonCallBack file.
                                    temp_wl = self.callbacks.get(cb, self.genericCallBacks.get(cb))(m[tag], temp_wl)
                                except Exception, e:
                                    pattern_name = self.patterns[self.tags_to_pattern[tag]].name
                                    raise Exception("Error on callback %s in pattern %s : %s - skipping" %
                                                    (self.callbacks[cb].name,
                                                     pattern_name, e))
                            # remove temporary tags
                            if self.tags_translation[tag].startswith('__'):
                                del temp_wl[self.tags_translation[tag]]
                    log.update(temp_wl)
                    # add the pattern's common Tags
                    log.update(matched_pattern.commonTags) 
                    # then add the normalizer's common Tags
                    log.update(self.commonTags)
                    # then add the taxonomy if relevant
                    if self.taxonomy:
                        log['taxonomy'] = self.taxonomy
                    # and finally, apply the final callbacks
                    for cb in self.finalCallbacks:
                        try:
                            log.update(self.callbacks.get(cb, self.genericCallBacks.get(cb))(None, log))
                        except Exception, e:
                            raise Exception("Cannot apply final callback %s : %r - skipping" % (cb, e))
                elif csv_patterns:
                    # this little trick makes the following line not type dependent
                    temp_wl = dict([ (u, log[u]) for u in log.keys() ])
                    ret = None
                    for csv_pattern in csv_patterns:
                        ret = csv_pattern.normalize(temp_wl[self.appliedTo])
                        if ret:
                            log.update(ret)
                            # then add the normalizer's common Tags
                            log.update(self.commonTags)
                            # then add the taxonomy if relevant
                            if self.taxonomy:
                                log['taxonomy'] = self.taxonomy
                            # and finally, apply the final callbacks
                            for cb in self.finalCallbacks:
                                try:
                                    log.update(self.callbacks.get(cb, self.genericCallBacks.get(cb))(None, log))
                                except Exception, e:
                                    raise Exception("Cannot apply final callback %s : %r - skipping" % (cb, e))
                            break
        return log

    def validate(self):
        """if the definition file comes with pattern examples, this method can
        be invoked to test these patterns against the examples.
        Note that tags not included in the "expectedTags" directives will not
        be checked for validation.
        @return: True if the normalizer is validated, raises a ValueError
                 describing the problem otherwise.
        """
        for p in self.patterns:
            for example in self.patterns[p].examples:
                w = { self.appliedTo : example.raw_line }
                if isinstance(self.patterns[p], Pattern):
                    w = self.normalize(w, do_not_check_prereq = True)
                elif isinstance(self.patterns[p], CSVPattern):
                    w = self.patterns[p].normalize(example.raw_line)
                    if w:
                        w.update(self.commonTags)
                        if self.taxonomy:
                            w['taxonomy'] = self.taxonomy
                        for cb in self.finalCallbacks:
                            try:
                                w.update(self.callbacks.get(cb, self.genericCallBacks.get(cb))(None, w))
                            except Exception, e:
                                raise Exception("Cannot apply final callback %s : %r - skipping" % (cb, e))
                for expectedTag in example.expected_tags.keys():
                    if isinstance(w.get(expectedTag), datetime):
                        svalue = str(w.get(expectedTag))
                    elif isinstance(w.get(expectedTag), int):
                        svalue = str(w.get(expectedTag))
                    else:
                        svalue = w.get(expectedTag)
                    if svalue != example.expected_tags[expectedTag]:
                        raise ValueError, 'Sample log "%s" does not match : expected %s -> %s, %s' % \
                                            (example,
                                             expectedTag,
                                             example.expected_tags[expectedTag],
                                             w.get(expectedTag))
        # No problem so far ? Awesome !
        return True

    def get_source(self):
        """gets the raw XML source for this normalizer."""
        return self.text_source
        
    def get_languages(self):
        """guesstimates the available languages from the description field and
        returns them as a list."""
        return self.description.keys()
        
# Documentation generator
def doc2RST(description, gettext = None):
    """ Returns a RestructuredText documentation from
        a parser description.
        @param description: the long description of the parser.
        @param gettext: is the gettext method to use.
                        You must configure gettext to use the domain 'normalizer' and
                        select a language.
                        eg. gettext.translation('normalizer', 'i18n', ['fr_FR']).ugettext
    """
    
    def escape(text):
        if isinstance(text, basestring):
            for c in "*\\":
                text.replace(c, "\\" + c)
        return text

    if not gettext:
        _ = lambda x: x
    else:
        _ = gettext

    template = _("""%(title)s

**Written by**

%(authors)s

Description
:::::::::::

%(description)s %(taxonomy)s

This normalizer can parse logs of the following structure(s):

%(patterns)s

Examples
::::::::

%(examples)s""")

    d = {}
    d['title'] = description['name'] + ' v.' + str(description['version'])
    d['title'] += '\n' + '-'*len(d['title'])
    d['authors'] = '\n'.join( ['* *%s*' % a for a in description['authors'] ] )
    d['description'] = escape(description['description']) or _('undocumented')
    d['taxonomy'] = ''
    if description["taxonomy"]:
        d['taxonomy'] = ("\n\n" +\
                         (_("This normalizer belongs to the category : *%s*") % description['taxonomy']) )
    d['patterns'] = ''
    d['examples'] = ''
    for p in description['patterns']:
        d['patterns'] +="""* %s""" % escape(p['pattern'])
        d['patterns'] += _(", where\n\n")
        for sub in p['substitutes']:
            d['patterns'] += _("  * **%s** is %s ") % (escape(sub), (p['tags'][p['substitutes'][sub]] or _('undocumented') ))
            if not p['substitutes'][sub].startswith('__'):
                d['patterns'] += _("(normalized as *%s*)") % p['substitutes'][sub]
            d['patterns'] += "\n"
        if description['commonTags'] or p['commonTags']:
            d['patterns'] += _("\n  Additionally, The following tags are automatically set:\n\n")
            for name, value in sum([description['commonTags'].items(),
                                    p['commonTags'].items()],
                                   []):
                d['patterns'] += "  * *%s* : %s\n" % (escape(name), value)
            d['patterns'] += "\n"
        if p.get('description') :
            d['patterns'] += "\n  %s\n" % p['description']
        d['patterns'] += "\n"
        for example in p['examples']:
            d['examples'] += _("* *%s*, normalized as\n\n") % escape(example['sample'])
            for tag, value in example['normalization'].items():
                d['examples'] += "  * **%s** -> %s\n" % (escape(tag), value)
            d['examples'] += '\n'
    return template % d

