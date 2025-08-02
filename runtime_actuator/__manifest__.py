{
    'name': 'Runtime Actuator',
    'version': '13.0.1.0',
    'summary': '通过在前端将python执行代码以文本的方式写入数据库，actuator模型可以识别并执行执行代码。',
    'description': """
        version 13.0.1.0 actuator为抽象模型
        version 13.0.1.1 actuator改为瞬息模型，直接crate后调用执行方法
    """,
    'author': 'Liao ziyang',
    'website': '',
    'license': '',
    'category': '',
    'depends': ['base','mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/menus.xml',
        'views/runtime_execution_content_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'qweb': [],
    'js': [],
    'css': [],
    'images': [],
    'sequence': 1,
}
