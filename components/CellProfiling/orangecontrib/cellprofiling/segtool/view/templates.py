# -*- coding: utf-8 -*-

def get_viewbox_label_html(txt0, txt1, misc=None, bgc='#000000', fgc='#10AA00'):
    html_template = """<body bgcolor="{bgc:}"><font color="{fgc:}">"""+\
            """<b>{txt0:} <em>{txt1:}</em></b>"""
    if misc is None:
        html_template += '</font>'
        ret = html_template.format(txt0=txt0, txt1=txt1, bgc=bgc, fgc=fgc)
    else:
        html_template += '{misc:}</font>'
        ret = html_template.format(txt0=txt0, txt1=txt1, misc=misc,
                                   bgc=bgc, fgc=fgc)
    return ret
