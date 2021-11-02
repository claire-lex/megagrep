# Megagrep dictionary
# Keywords in .NET
#
# Source: OWASP Code Review Guide v2

[input]
request.accesstypes
request.httpmethod
request.cookies
request.url
request.browser
request.querystring
request.certificate
request.urlreferrer
request.files
request.item
request.rawurl
request.useragent
request.headers
request.form
request.servervariables
request.userlanguages
request.TotalBytes
request.BinaryRead

[output]
response.write
HttpUtility
HtmlEncode
UrlEncode
innerText
innerHTML
<%=
Console.WriteLine
System.Diagnostics.*

[sql]
select from
insert
update
delete from where
delete
executestatement
executeSQL
setfilter
executeQuery
GetQueryResultInXML
adodb
sqloledb
sql server
driver
Server.CreateObject
.Provider
System.Data.sql
ADODB.recordset
New OleDbConnection
ExecuteReader
DataSource
SqlCommand
MicrosoftJet
SqlDataReader
ExecuteReader
SqlDataAdapter
StoredProcedure

[cookies]
System.Net.Cookie
HTTPOnly
document.cookie

[html]
HtmlEncode
URLEncode
<applet>
<frameset>
<embed>
<frame>
<html>
<iframe>
<img>
<style>
<layer>
<ilayer>
<meta>
<object>
<frame security
<iframe security

[controls]
htmlcontrols.htmlinputhidden
webcontrols.hiddenfield
webcontrols.hyperlink
webcontrols.textbox
webcontrols.label
webcontrols.linkbutton
webcontrols.listbox
webcontrols.checkboxlist
webcontrols.dropdownlist

[config]
requestEncoding
responseEncoding
Trace
authorization
compilation
webcontrols.linkbutton
webcontrols.listbox
webcontrols.checkboxlist
webcontrols.dropdownlist
CustomErrors
httpCookies
httpHandlers
httpRuntime
sessionState
maxRequestLength
Debug
forms protection
appSettings
ConfigurationSettings
connectionStrings
authentication mode
Allow
Deny
Credentials
identity impersonate
timeout
remote
Application_OnAuthenticateRequest
Application_OnAuthorizeRequest
Session_OnStart
Session_OnEnd
validateRequest
enableViewState
enableViewStateMac

[design]
Public
Serializable
AllowPartiallyTrustedCallersAttribute
GetObjectData
System.Reflection
StrongNameIdentity
StrongNameIdentityPermission
catch
finally
trace enabled

[crypto]
RNGCryptoServiceProvider
SHA*1 # Guide suggests "SHA" but Megagrep returns any word containing "sha"
MD5
base64
3*DES # Guide suggests "DES" but Megagrep returns any word containing "des"
RC2
System.Random
Random
System.Security.Cryptography

[authorization]
RequestMinimum
RequestOptional
Assert
Debug.Assert
CodeAccessPermission
MemberAccess
ControlAppDomain
UnmanagedCode
SkipVerification
ControlEvidence
SerializationFormatter
ControlPrincipal
ControlDomainPolicy
ControlPolicy

[legacy]
printf
strcpy
