import base64
import tempfile
import flask
from vardb.datamodel import attachment

# Base 64 representation of a png with the ella logo
B64_DATA = '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'

def test_attachments(session, client):
    # Create temporary file to upload
    f = tempfile.NamedTemporaryFile('w', delete=False)
    f.write(base64.b64decode(B64_DATA))
    f.close()

    # Upload file (can't use client.post, because it dumps data to json)
    with client.app.test_client() as c:
       client.ensure_logged_in(c, "testuser1")
       r = c.post('/api/v1/attachments/upload/', data={'file': (open(f.name), 'ella.png')})

    assert r.status_code == 200
    attachment_obj = session.query(attachment.Attachment).one()
    assert attachment_obj.filename == "ella.png"
    assert attachment_obj.extension == "png"
    assert attachment_obj.mimetype == "image/png"

    # Download file
    r = client.get('/api/v1/attachments/'+str(attachment_obj.id))

    assert r.status_code == 200
    assert r.get_data() == base64.b64decode(B64_DATA)




