# -*- coding: utf-8 -*-
{
    'name': "Acm Import Qweb Temlplate File",
    'description': """
        在不重启系统的情况下加载模板文件到系统中，通过上传qweb模板文件，导入到数据库ir_ui_view表中, 和手动创建qweb视图虽然区别不大，但增加了关联记录的页面并管理。
        当前版本只适配导入Qweb视图。
    """,
    'summary': "",
    'author': "Liao Ziyang",
    'website': "",
    'category': 'ACM-APP',
    'version': '13.0.1.0',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': ['base','mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/create_record.xml',
        'views/import_view_file_views.xml',
        'wizard/file_import_wizard_views.xml',
        'wizard/delete_file_wizard_views.xml',
    ],
    'demo': [
    ],
    
}
