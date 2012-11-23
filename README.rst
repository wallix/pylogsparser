LogsParser
==========

Description
:::::::::::

LogsParser is an opensource python library created by Wallix ( http://www.wallix.org ).
It is used as the core mechanism for logs tagging and normalization by Wallix's LogBox
( http://www.wallix.com/index.php/products/wallix-logbox ).

Logs come in a variety of formats. In order to parse many different types of
logs, a developer used to need to write an engine based on a large list of complex
regular expressions. It can become rapidly unreadable and unmaintainable.

By using LogsParser, a developer can free herself from the burden of writing a
log parsing engine, since the module comes in with "batteries included".
Furthermore, this engine relies upon XML definition files that can be loaded at
runtime. The definition files were designed to be easily readable and need very
little skill in programming or regular expressions, without sacrificing
powerfulness or expressiveness.

Purpose
:::::::

The LogsParser module uses normalization definition files in order to tag
log entries. The definition files are written in XML.

The definition files allow anyone with a basic understanding of regular
expressions and knowledge of a specific log format to create and maintain
a customized pool of parsers.

Basically a definition file will consist of a list of log patterns, each
composed of many keywords. A keyword is a placeholder for a notable and/or 
variable part in the described log line, and therefore associated to a tag
name. It is paired to a tag type, e.g. a regular expression matching the
expected value to assign to this tag. If the raw value extracted this way needs
further processing, callback functions can be applied to this value.

This format also allows to add useful meta-data about parsed logs, such as
extensive documentation about expected log patterns and log samples.

Format Description
------------------

A normalization definition file must strictly follow the specifications as
they are detailed in the file normalizer.dtd .

A simple template is provided to help parser writers get started with their
task, called normalizer.template.

Most definition files will include the following sections :

* Some generic documentation about the parsed logs : emitting application,
  application version, etc ... (non-mandatory)
* the definition file's author(s) (non-mandatory)
* custom tag types (non-mandatory)
* callback functions (non-mandatory)
* Prerequisites on tag values prior to parsing (non-mandatory)
* Log pattern(s) and how they are to be parsed
* Extra tags with a fixed value that should be added once the parsing is done
  (non-mandatory)

Root
....

The definition file's root must hold the following elements :

* the normalizer's name.
* the normalizer's version.
* the flags to apply to the compilation of regular expressions associated with
  this parser : unicode support, multiple lines support, and ignore case.
* how to match the regular expression : from the beginning of the log line (match)
  or from anywhere in the targeted tag (search)
* the tag value to parse (raw, body...)
* the service taxonomy, if relevant, of the normalizer. See the end of this
  document for more details.
* the optional expandWhitespaces value. If set to "yes", spaces or carriage returns
   in a pattern will be converted to match any whitespace character (line feed, tab, etc). 
   This is to maintain the readability of multiline patterns.

Default tag types
.................

A few basic tag types are defined in the file common_tagTypes.xml . In order
to use it, it has to be loaded when instantiating the Normalizer class; see the
class documentation for further information.

Here is a list of default tag types shipped with this library.

* Anything : any character chain of any length.
* Integer
* EpochTime : an EPOCH timestamp of arbitrary precision (to the second and below).
* syslogDate : a date as seen in syslog formatted logs (example : Mar 12 20:13:23)
* URL
* MACAddress
* Email
* IP
* ZuluTime : a "Zulu Time"-type timestamp (example : 2012-12-21T13:45:05)


Custom Tag Types
................

It is always possible to define new tag types in a parser definition file, and
to overwrite default ones. To define a new tag type, the following elements are
needed :

* a type name. This will be used as the type reference in log patterns.
* the python type of the expected result : this element is not used yet and can
  be safely set to anything.
* a non-mandatory description.
* the regular expression defining this type.

Callback Functions
..................

One might want to transform a raw value after it has been extracted from a pattern:
the syslog normalizer converts the raw log timestamp into a python datetime object,
for example.

In order to do this, the <callback> tag must be used to define a callback function.

<callback> requires a function name as a mandatory attribute. Its text defines the
function body as in python, meaning the PEP8 indentation rules are to be followed. 

When writing a callback function, the following rules must be respected :

* Your callback function will take ONLY two arguments: **value** and **log**.
  "value" is the raw value extracted from applying the log pattern to the log,
  and "log" is the dictionary of the normalized log in its current state (prior
  to normalization induced by this parser definition file).
* Your callback function can modify the "log" argument (especially assign
  the transformed value to the concerned tag name) and must not return anything.
* Your callback function has a restricted access to the following facilities: ::

   "list", "dict", "tuple", "set", "long", "float", "object",
   "bool", "callable", "True", "False", "dir",
   "frozenset", "getattr", "hasattr", "abs", "cmp", "complex",
   "divmod", "id", "pow", "round", "slice", "vars",
   "hash", "hex", "int", "isinstance", "issubclass", "len",
   "map", "filter", "max", "min", "oct", "chr", "ord", "range",
   "reduce", "repr", "str", "unicode", "basestring", "type", "zip", "xrange", "None",
   "Exception"  

* Importing modules is therefore forbidden and impossible. The *re* and *datetime*
  modules are available for use as if the following lines were present: ::

   import re
   from datetime import datetime
   
* In version 0.4, the "extras" package is introduced. It allows more freedom in 
  what can be used in callbacks. It also increases execution speed in some 
  cases; typically when you need to use complex objects in your callback like 
  a big set or a big regular expression. In the old approach, this object 
  would be created each time the function is called; by deporting the object's
  creation in the extras package it is created once and for all. See the modules
  in logsparser.extras for use cases.

Default callbacks
.................

As with default tag types, a few generic callbacks are defined in the file 
common_callBacks.xml . Currently they are meant to deal with common date 
formattings. Therefore they will automatically set the "date" tag. In order to 
use it, the callbacks file has to be loaded when instantiating the Normalizer 
class; see the class documentation for further information.

In case of name collisions, callbacks defined in a normalizer description file 
take precedence over common callbacks.

Here is a list of default callbacks shipped with this library. 

* MM/dd/YYYY hh:mm:ss : parses dates such as 04/13/2010 14:23:56
* dd/MMM/YYYY:hh:mm:ss : parses dates such as 19/Jul/2009 12:02:43
* MMM dd hh:mm:ss : parses dates such as Oct 23 10:23:12 . The year is guessed 
  so that the resulting date is the closest in the past.
* DDD MMM dd hh:mm:ss YYYY : parses dates such as Mon Sep 11 09:13:54 2011
* YYYY-MM-DD hh:mm:ss : parses dates such as 2012-12-21 00:00:00
* MM/DD/YY, hh:mm:ss : parses dates such as 10/23/11, 07:24:04 . The year is 
  assumed to be in the XXIst century.
* YYMMDD hh:mm:ss:  parses dates such as 070811 17:23:12 . The year is assumed 
  to be in the XXIst century.
* ISO8601 : converts a combined date and time in UTC expressed according to the 
  ISO 8601 standard. Also commonly referred to as "Zulu Time".
* EPOCH : parses EPOCH timestamps
* dd-MMM-YYYY hh:mm:ss : parses dates such as 28-Feb-2010 23:15:54

Final callbacks
...............

One might want to wait until a pattern has been fully applied before processing
data : if for example you'd like to tag a log with a value made of a concatenation of
other values, and so on. It is possible to specify a list of callbacks to apply
at the end of the parsing with the XML tag "finalCallbacks".

Such callbacks will follow the mechanics described above, with one notable change:
they will be called with the argument "value" set to None. Therefore, you have
to make sure your callback will work correctly that way.

There are a few examples of use available : in the test_normalizer.py test code,
and in the deny_all normalizer.

Pattern definition
..................

A definition file can contain as many log patterns as one sees fit. These patterns
are simplified regular expressions and applied in alphabetical order of their names,
so it is important to name them so that the more precise patterns are tried
before the more generic ones.

A pattern is a "meta regular expression", which means that every syntactic rule from
python's regular expressions are to be followed when writing a pattern, especially
escaping special characters. To make the patterns easier to read than an obtuse
regular expression, keywords act as "macros" and correspond to a part of the log
to assign to a tag.

A log pattern has the following components:

* A name.
* A non-mandatory description of the pattern's context.
* The pattern itself, under the tag "text".
* The tags as they appear in the pattern, the associated name once the normalization
  is over, and the callback functions to eventually call on their raw values
* Non-mandatory log samples. These can be used for self-validation.

If a tag name starts with __ (double underscore), this tag won't be added to the
final normalized dictionary. This allows to create temporary tags that will
typically be used in conjunction to a series of callback functions, when the
original raw value has no actual interest.

To define log patterns describing a CSV-formatted message, one must add the
following attributes in the tag "text":

* type="csv"
* separator="," or the relevant separator character
* quotechar='"' or the relevant quotation character

Tags are then defined normally. Pylogsparser will deal automatically with missing
fields.


Best practices
..............

* Order your patterns in decreasing order of specificity. Not doing so might
  trigger errors, as more generic patterns will match earlier.
* The more precise your tagTypes' regular expressions, the more accurate your
  parser will be.
* Use description tags liberally. The more documented a log format, the better.
  Examples are also invaluable.

Tag naming convention
.....................

The tag naming convention is lowercase, underscore separated words. It is strongly
recommended to stick to that naming convention when writing new normalizers
for consistency's sake. In case of dynamic fields, it is advised to make sure
dynamic naming follows the convention. There's an example of this in 
MSExchange2007MessageTracking.xml; see the callback named "decode_MTLSourceContext".

Log contains common informations such as username, IP address, informations about
transport protocol... In order to ease log post-processing we must define a common
method to name those tags and not deal for example with a series of "login, user,
username, userid" all describing a user id.
The alphabetical list below is a series of tag names that must be used when relevant.

- action : action taken by a component such as DELETED, migrated, DROP, open.
- bind_int : binding interface for a network service.
- dest_host : hostname or FQDN of a destination host.
- dest_ip : IP address of a destination host.
- dest_mac : MAC address of a destination host.
- dest_port : destination port of a network connection.
- event_id : id describing an event.
- inbound_int : network interface for incoming data.
- len : a data size.
- local_host : hostname or FQDN of the local host.
- local_ip : IP adress of the local host.
- local_mac : MAC address of the local host.
- local_port : listening port of a local service.
- message_id : message or transaction id.
- message_recipient : message recipient id.
- message_sender : message sender id.
- method : component access method such as GET, key_auth.
- outbound_int : network interface for outgoing data.
- protocol : network or software protocol name or numeric id such as TCP, NTP, SMTP.
- source_host : hostname or FQDN of a source host.
- source_ip : IP address of a source host.
- source_mac : MAC address of a source host.
- source_port : source port of a network connection.
- status : component status such as FAIL, success, 404.
  see below for a complete list.
- url : an URL as defined in rfc1738. (scheme://netloc/path;parameters?query#fragment)
- user : a user id.

Service taxonomy
................

As of pylogsparser 0.4 a taxonomy tag is added to relevant normalizers. It helps
classifying logs by service type, which can be useful for reporting among other
things. Here is a list of identified services; suggestions and improvements are
welcome !

+-----------+----------------------------------------+------------------------+
| Service   | Description                            | Normalizers            |
+===========+========================================+========================+
| access    | A service dealing with authentication  | Fail2ban               |
| control   | and/or authorization                   | pam                    |
|           |                                        | sshd                   |
|           |                                        | wabauth                |
+-----------+----------------------------------------+------------------------+
| antivirus | A service dealing with malware         | bitdefender            |
|           | detection and prevention               | symantec               |
+-----------+----------------------------------------+------------------------+
| database  | A database service such as mySQLd,     | mysql                  |
|           | postmaster (postGRESQL), ...           |                        |
+-----------+----------------------------------------+------------------------+
| address   | A service in charge of network address | dhcpd                  |
|assignation| assignations                           |                        |
+-----------+----------------------------------------+------------------------+
| name      | A service in charge of network names   | named                  |
| resolution| resolutions                            | named-2                |
+-----------+----------------------------------------+------------------------+
| firewall  | A service in charge of monitoring      | LEA                    |
|           | and filtering network traffic          | arkoonFAST360          |
|           |                                        | deny_event             |
|           |                                        | netfilter              |
+-----------+----------------------------------------+------------------------+
| file      | A file transfer service                | xferlog                |
| transfer  |                                        |                        |
+-----------+----------------------------------------+------------------------+
| hypervisor| A virtualization platform service      | VMWare_ESX4-ESXi4      |
|           |                                        |                        |
+-----------+----------------------------------------+------------------------+
| mail      | A mail server                          | MSExchange2007-        |
|           |                                        | MessageTracking        |
|           |                                        | postfix                |
+-----------+----------------------------------------+------------------------+
| web proxy | A service acting as an intermediary    | dansguardian           |
|           | between clients and web resources;     | deny_traffic           |
|           | access control and content filtering   | squid                  |
|           | can also occur                         |                        |
+-----------+----------------------------------------+------------------------+
| web server| A service exposing web resources       | IIS                    |
|           |                                        | apache                 |
+-----------+----------------------------------------+------------------------+
