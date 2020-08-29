# encoding: utf-8
import argparse
import sys
import os
import webbrowser

from workflow import Workflow, web, notify, PasswordNotFound
from workflow.workflow import ICON_ROOT, ICON_WARNING, ICON_INFO

ICON_DOCUMENT = os.path.join(ICON_ROOT, 'GenericDocumentIcon.icns')


def main(workflow):
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--use-app', dest='use_app', type=bool, default=False)
    parser.add_argument('-d', '--domain', dest='domain')
    parser.add_argument('-k', '--setkey', dest='apikey', action='store_true')
    parser.add_argument('-t', '--only-match-titles', dest='only_match_titles', action='store_true')
    parser.add_argument('query', nargs='?', default=None)
    args = parser.parse_args(workflow.args)

    if args.domain:
        domain = args.domain.strip()
    else:
        domain = 'quip.com'

    if args.apikey:
        if not args.query:
            webbrowser.open('https://' + domain + '/dev/token')
            return 0

        workflow.save_password('quip_api_key', args.query)
        notify.notify('Quip API key set')
        return 0

    try:
        api_key = workflow.get_password('quip_api_key')
    except PasswordNotFound:  # API key has not yet been set
        workflow.add_item('No API key set.', 'Please use set-quip-key to set your Quip API key.', valid=False,
                          icon=ICON_WARNING)
        workflow.send_feedback()
        return 0

    if args.query:
        search_api = 'https://platform.' + domain + '/1/threads/search'
        request = {'query': args.query.strip(), 'only_match_titles': args.only_match_titles, 'count': 50}
        auth_headers = {'Authorization': 'Bearer {0}'.format(api_key)}
        response = web.get(search_api, request, headers=auth_headers).json()

        if not response:  # we have no data to show, so show a warning and stop
            workflow.add_item('No documents found', icon=ICON_WARNING)
            workflow.send_feedback()
            return 0

        for row in response:
            thread = row['thread']
            title = thread['title']
            link = thread['link']
            uid = thread['id']
            if args.use_app:
                arg = 'quip://' + uid
                subtitle = 'Open in Quip'
                modifier_subtitles = {'cmd': 'Open in Browser'}
            else:
                arg = link
                subtitle = 'Open in Browser'
                modifier_subtitles = {'cmd': 'Open in Quip'}
            workflow.add_item(title=title, arg=arg, subtitle=subtitle, modifier_subtitles=modifier_subtitles,
                              quicklookurl=link, icon=ICON_DOCUMENT, uid=uid, valid=True)
    else:
        workflow.add_item('Enter a search term', valid=False, icon=ICON_INFO)

    workflow.send_feedback()


if __name__ == u"__main__":
    wf = Workflow(normalization='NFD', update_settings={'github_slug': 'cameronsstone/alfred-quip-workflow', 'frequency': 1, })
    sys.exit(wf.run(main))
