odoo.define('approval.my_widget', function (require) {
"use strict";

// 导入依赖
var AbstractField = require('web.AbstractField');
var fieldRegistry = require('web.field_registry');
var core = require('web.core');
var qweb = core.qweb;

// 创建自定义 Widget
var MyCustomWidget = AbstractField.extend({
    className: 'o_my_custom_widget',
    supportedFieldTypes: ['char'],  // 支持的字段类型

    // 初始化
    init: function (parent, name, record, options) {
        this._super.apply(this, arguments);
        // 自定义初始化逻辑
    },

    // 渲染只读模式
    _render: function () {
        var value = this.value || '';
        this.$el.empty();

        // 使用模板渲染（推荐）
        this.$el.append($(qweb.render('MyWidgetTemplate', {
            value: value,
            color: this._pickColor(value)
        })));

        // 或直接操作 DOM
        // this.$el.append(`<div style="color:${this._pickColor(value)}">${value}</div>`);
    },

    // 自定义方法
    _pickColor: function(value) {
        return value.length > 5 ? 'green' : 'red';
    }
});

// 注册到字段注册表
fieldRegistry.add('my_custom_widget', MyCustomWidget);

return MyCustomWidget;
});