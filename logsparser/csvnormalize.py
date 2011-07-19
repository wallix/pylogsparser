import csv
import re
from normalizer import TagType, Tag, CallbackFunction

class CSVPattern(object):
    def __init__(self,
                 name,
                 pattern,
                 separator = ',',
                 quotechar = '"',
                 tags = {},
                 description = '',
                 commonTags = {},
                 examples = []):
        self.name = name
        self.pattern = pattern
        self.separator = separator
        self.quotechar = quotechar
        self.tags = tags
        self.description = description
        self.examples = examples
        self.commonTags = commonTags
        _fields = self.pattern.split(self.separator)
        self.fields = [f.strip() for f in _fields]
        self.check_count = len(self.fields)

    def check_type(self, data):
        # TODO: re flags
        for tag in self.tags:
            r = re.compile(self.tags[tag].tagtype.regexp)
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
        return data

    def apply_cb(self, data):
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
            # Check expected for for fileds
            data = self.check_type(dict(zip(self.fields, data)))
            if data:
                # Apply callbacks
                data = self.apply_cb(data)
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
    


if __name__ == '__main__':

    tt1 = TagType(name='AnyThing',
                 ttype=str,
                 regexp = '.*')
    
    tt2 = TagType(name='AnyThing',
                 ttype=int,
                 regexp = '[1-9]*')

    t1 = Tag(name='tagf1',
             tagtype = tt1,
             substitute = 'F1')

    t2 = Tag(name='tagf2',
             tagtype = tt1,
             substitute = 'F2')

    t3 = Tag(name='tagf3',
             tagtype = tt2,
             substitute = 'F3')
    
    t4 = Tag(name='tagf4',
             tagtype = tt1,
             substitute = 'F4')

    p_tags = {}
    for t in (t1, t2, t3, t4):
        p_tags[t.name] = t

    a = CSVPattern('test', 'F1,F2,F3,F4', tags = p_tags)
    ret = a.normalize('bonjour,le,,demain')
    print ret
