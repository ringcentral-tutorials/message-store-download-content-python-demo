from ringcentral import SDK
from ringcentral.http.api_exception import ApiException
import os, time

from dotenv import Dotenv

dotenv = Dotenv(".env")
os.environ.update(dotenv)

if os.getenv("ENVIRONMENT") == "sandbox":
    dotenv = Dotenv("./environment/.env-sandbox")
else:
    dotenv = Dotenv("./environment/.env-production")
os.environ.update(dotenv)

rcsdk = SDK(os.getenv("RC_CLIENT_ID"), os.getenv("RC_CLIENT_SECRET"), os.getenv("RC_SERVER_URL"))
platform = rcsdk.platform()
platform.login(os.getenv("RC_USERNAME"), os.getenv("RC_EXTENSION"), os.getenv("RC_PASSWORD"))

def main():
    read_message_store_message_content()

def read_message_store_message_content():
    resp = platform.get('/restapi/v1.0/account/~/extension/~/message-store',
        {
            'dateFrom': '2018-01-01T00:00:00.000Z',
            'dateTo': '2018-12-31T23:59:59.999Z'
        })
    contentPath = os.getcwd() + "/content/"
    try:
        os.mkdir(contentPath)
    except OSError:
        print ("Creation of the directory %s failed" % contentPath)
    # Limit API call to ~40 calls per minute to avoid exceeding API rate limit.
    timePerApiCall = 1200
    for record in resp.json().records:
        if record.attachments != None:
            for attachment in record.attachments:
                fileExt = getFileExtensionFromMimeType(attachment.contentType)
                if record.type == "VoiceMail":
                    if attachment.type == "AudioRecording":
                        fileName = ("voicemail_recording_%s%s" % (record.attachments[0].id, fileExt))
                    elif attachment.type == "AudioTranscription" and record.vmTranscriptionStatus == "Completed":
                        fileName = ("voicemail_transcript_%s.txt" % record.attachments[0].id)
                elif record.type == "Fax":
                    fileName = ("fax_attachment_%s%s" % (attachment.id, fileExt))
                elif record.type == "SMS":
                    if attachment.type == "MmsAttachment":
                        fileName = ("mms_attachment_%s%s" % (record.attachments[0].id, fileExt))
                    else:
                        fileName = ("sms_text_%s.txt" % (record.attachments[0].id))
                try:
                    res = platform.get(attachment.uri)
                    start = time.time()
                    file = open(("%s%s" % (contentPath, fileName)),'w')
                    file.write(res.body())
                    file.close()
                    end = time.time()
                    consumed = end - start
                    if consumed < timePerApiCall:
                        time.sleep((timePerApiCall - consumed)/1000)
                except ApiException as e:
                    print (e.message)

def getFileExtensionFromMimeType(mimeType):
    switcher = {
        "text/html": "html",
        "text/css": ".css",
        "text/xml": ".xml",
        "text/plain": ".txt",
        "text/x-vcard": ".vcf",
        "application/msword": ".doc",
        "application/pdf": ".pdf",
        "application/rtf": ".rtf",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.ms-powerpoint": ".ppt",
        "application/zip": ".zip",
        "image/tiff": ".tiff",
        "image/gif": ".gif",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/x-ms-bmp": ".bmp",
        "image/svg+xml": ".svg",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "video/3gpp": ".3gp",
        "video/mpeg": ".mpeg",
        "video/quicktime": ".mov",
        "video/x-flv": ".flv",
        "video/x-ms-wmv": ".wmv",
        "video/mp4": ".mp4"
    }
    return switcher.get(mimeType, ".unknown")

main()
