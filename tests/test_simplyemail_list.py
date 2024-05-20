from Helpers import (
    helpers, Download, Parser, CanarioAPI, EmailFormat,
    HtmlBootStrapTheme, Converter, VerifyEmails
)
from Common import TaskController
from Modules import (
    SearchPGP, AskSearch, YahooSearch, WhoisAPISearch,
    RedditPostSearch, FlickrSearch
)
import os

# Проверка функций helpers
assert helpers.color('test')
assert helpers.color('test', firewall=True)
assert helpers.color('test', warning=True)
assert helpers.format_long(
    "test", "TESSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS"
)
assert helpers.directory_listing('/')


# Тестирование TaskController
def test_taskcontrollers():
    Task = TaskController.Conducter()
    Task.load_modules()
    for x in Task.modules:
        l = Task.modules[x]
        mod = l.ClassName('test.com', verbose=True)
    Task.ListModules()
    Task.title()

    Task.ConsumerList = ['alex@test.com', 'alex@test.com', 'alex2@gmail.com', 'alex2@test.com']
    Task.HtmlList = ['alex@test.com', 'alex@test.com', 'alex2@gmail.com', 'alex2@test.com']
    finallist, htmllist = Task.CleanResults('test.com')
    assert 'alex@test.com' in finallist
    assert 'alex2@test.com' in finallist
    assert 'alex2@gmail.com' not in finallist
    assert finallist.count("alex@test.com") < 2
    assert 'alex@test.com' in htmllist
    assert 'alex2@test.com' in htmllist
    assert 'alex2@gmail.com' not in htmllist
    assert htmllist.count("alex@test.com") < 2


def test_searchpgp():
    s = SearchPGP.ClassName('verisgroup.com', verbose=True)
    FinalOutput, HtmlResults, JsonResults = s.execute()
    assert 'jmacovei@verisgroup.com' in FinalOutput


def test_asksearch():
    s = AskSearch.AskSearch('gmail.com', verbose=True)
    FinalOutput, HtmlResults, JsonResults = s.execute()
    assert len(FinalOutput) > 0


def test_yahoosearch():
    s = YahooSearch.YahooEmailSearch('gmail.com', verbose=True)
    FinalOutput, HtmlResults, JsonResults = s.execute()
    assert len(FinalOutput) > 0


def test_whoisapi():
    s = WhoisAPISearch.WhoisAPISearch('verisgroup.com', verbose=True)
    FinalOutput, HtmlResults, JsonResults = s.execute()
    assert 'abuse@web.com' in FinalOutput


def test_redditsearch():
    s = RedditPostSearch.ClassName('gmail.com', verbose=True)
    FinalOutput, HtmlResults, JsonResults = s.execute()
    # assert '@gmail.com' in FinalOutput
    # Look into this issue


def test_flickrsearch():
    s = FlickrSearch.FlickrSearch('microsoft.com', verbose=True)
    FinalOutput, HtmlResults, JsonResults = s.execute()


def test_downloads():
    ua = helpers.get_user_agent()
    dl = Download.Download(True)
    html = dl.requesturl('http://google.com', ua, timeout=2, retrytime=3, statuscode=False)
    dl.GoogleCaptchaDetection(html)
    f, download = dl.download_file('http://www.sample-videos.com/doc/Sample-doc-file-100kb.doc', '.pdf')
    dl.delete_file(f)


def test_canario():
    c = CanarioAPI.Canary('thisshouldnotworkapikey')


def test_verifyemails():
    em1 = ['test@gmail.com']
    em2 = ['alex@gmail.com']
    v = VerifyEmails.VerifyEmail(em1, em2, 'gmail.com')
    v.get_mx()
    assert 'gmail' in v.mxhost['Host']
    v.verify_smtp_server()


def test_converter():
    p = os.path.dirname(os.path.realpath('.')) + '/SimplyEmail/tests/'
    c = Converter.Converter(verbose=True)
    text = c.convert_docx_to_txt(p + 'Test-DOCX.docx')
    assert text
    assert 'How to Design and Test' in text
    text = c.convert_doc_to_txt(p + 'Test-DOC.doc')
    assert text
    assert 'How to Design and Test' in text
    text = c.convert_pdf_to_txt(p + 'Test-PDF.pdf')
    assert text
    assert 'How to Design and Test' in text
    text = c.convert_zip_to_text(p + 'Test-PPTX.pptx')
    assert text
    assert 'Test SLIDE' in text
    assert 'Test SLIDE 2' in text
    assert 'Test SLIDE 3' in text


def test_htmlbootstrap():
    em = [
        "{'Email': 'alex@test.com', 'Source': 'gmail'}",
        "{'Email': 'alex2@test.com', 'Source': 'Canary Paste Bin'}",
        "{'Email': 'alex3@test.com', 'Source': 'testing'}"
    ]
    h = HtmlBootStrapTheme.HtmlBuilder(em, "test.com")
    h.build_html()
    assert '<td>alex@test.com</td>' in h.html
    assert '<td>alex2@test.com</td>' in h.html
    assert '<td>alex3@test.com</td>' in h.html
    assert '<td>gmail</td>' in h.html
    assert '<td>Canary Paste Bin</td>' in h.html
    assert '<td>testing</td>' in h.html
    assert 'Canary (PasteBin) search detected Email(s)' in h.html
    p = os.path.dirname(os.path.realpath('.'))
    h.output_html(p)


def test_parser():
    raw = """
    alex //
    test //...dfdfsf
    data !@#$%^%&^&*()
    <em>alex@verisgroup.com</em>
    <em> alex@verisgroup.com </em>
    <tr>alex@verisgroup.com</tr>
    <></><><><><><>
    """
    p = Parser.Parser(raw)
    p.remove_unicode()
    finaloutput, htmlresults = p.extended_clean('test')


def test_emailformat():
    em = EmailFormat.EmailFormat('verisgroup.com', Verbose=True)
    name = em.build_name(['alex', 'test'], "{first}.{last}")
    assert name == 'alex.test'
    cleannames = [['alex', 'test'], ['alex', 'man'], ['alex', 'dude'], ['mad', 'max']]
    domain = 'verisgroup.com'
    finalemails = ['mmax@verisgroup.com']
    result = em.email_detect(cleannames, domain, finalemails)
    assert result[0] == '{f}{last}'
    finalemails = ['m.max@verisgroup.com']
    result = em.email_detect(cleannames, domain, finalemails)
    assert result[0] == '{f}.{last}'
    finalemails = ['madmax@verisgroup.com']
    result = em.email_detect(cleannames, domain, finalemails)
    assert result[0] == '{first}{last}'
    finalemails = ['mad.max@verisgroup.com']
    result = em.email_detect(cleannames, domain, finalemails)
    assert result[0] == '{first}.{last}'
    finalemails = ['mad.m@verisgroup.com']
    result = em.email_detect(cleannames, domain, finalemails)
    assert result[0] == '{first}.{l}'
    finalemails = ['madm@verisgroup.com']
    result = em.email_detect(cleannames, domain, finalemails)
    assert result[0] == '{first}{l}'
    finalemails = ['mad_max@verisgroup.com']
    result = em.email_detect(cleannames, domain, finalemails)
    assert result[0] == '{first}_{last}'
    finalemails = ['mad@verisgroup.com']
    result = em.email_detect(cleannames, domain, finalemails)
    assert result[0] == '{first}'

    fm = '{f}{last}'
    emails = em.email_builder(cleannames, domain, fm)
    assert 'mmax@verisgroup.com' in emails
    fm = '{f}.{last}'
    emails = em.email_builder(cleannames, domain, fm)
    assert 'm.max@verisgroup.com' in emails
    fm = '{first}{last}'
    emails = em.email_builder(cleannames, domain, fm)
    assert 'madmax@verisgroup.com' in emails
    fm = '{first}.{last}'
    emails = em.email_builder(cleannames, domain, fm)
    assert 'mad.max@verisgroup.com' in emails
    fm = '{first}.{l}'
    emails = em.email_builder(cleannames, domain, fm)
    assert 'mad.m@verisgroup.com' in emails
    fm = '{first}{l}'
    emails = em.email_builder(cleannames, domain, fm)
    assert 'madm@verisgroup.com' in emails
    fm = '{first}_{last}'
    emails = em.email_builder(cleannames, domain, fm)
    assert 'mad_max@verisgroup.com' in emails
    fm = '{first}'
    emails = em.email_builder(cleannames, domain, fm)
    assert 'mad@verisgroup.com' in emails
