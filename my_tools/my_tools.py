import pytz


def _create_tracking_info(field_name, ov, nv):
    h_li = '<li>{}:<br>&nbsp;&nbsp;&nbsp;<span>{} </span><span class="fa fa-long-arrow-right" role="img" aria-label="Changed" title="Changed"/><span> {}</span></li>'.format(
        field_name, ov, nv)
    return h_li


def create_default_tracking_write(self, tracking_title, vals, ignore_fields=[], fields_mapped={}):
    """
    缺少对某种对多字段的新建删除记录的判断处理
    """
    """
    ADD:
    {'sequence': {'name': 'Sequence', 'old': 1, 'new': 12}, 'role': {'name': 'role', 'old': '初审', 'new': '初审12'}, 
    'approval_opinion': {'name': 'Approval Opinion', 'old': '', 'new': '666'}, 
    'group_ids': {'name': 'Authorized Groups', 'old': 'Acumen Groups / AcumenFDUser, Acumen Groups / AcumenMrpUser, 库存 / 用户', 'new': 'Acumen Groups / AcumenFDUser, Acumen Groups / AcumenMrpUser'}, 
    'user_ids': {'name': 'Authorized user', 'old': '', 'new': 'Administrator'}}

    DEL:
    {'sequence': {'name': 'Sequence', 'old': 12, 'new': 1}, 'role': {'name': 'role', 'old': '初审12', 'new': '初审'}, 
    'approval_opinion': {'name': 'Approval Opinion', 'old': '666', 'new': ''}, 
    'group_ids': {'name': 'Authorized Groups', 'old': 'Acumen Groups / AcumenFDUser, Acumen Groups / AcumenMrpUser', 'new': ''}, 
    'user_ids': {'name': 'Authorized user', 'old': 'Administrator', 'new': ''}}

    CSS:
    <t t-name="mail.widget.Thread.MessageTracking">
    <ul class="o_mail_thread_message_tracking">
        <t t-foreach='message.getTrackingValues()' t-as='value'>
            <li>
                <t t-esc="value.changed_field"/>:
                <t t-if="value.old_value">
                    <span> <t t-esc="value.old_value || ((value.field_type !== 'boolean') and '')"/> </span>
                    <span t-if="value.old_value !== value.new_value" class="fa fa-long-arrow-right" role="img" aria-label="Changed" title="Changed"/>
                </t>
                <span t-if="value.old_value !== value.new_value">
                    <t t-esc="value.new_value || ((value.field_type !== 'boolean') and '')"/>
                </span>
            </li>
        </t>
    </ul>
    </t>
    """
    self.ensure_one()
    fields_mapped.update({'message_channel_ids': 'name', 'message_partner_ids': 'name'})
    model_fields = self.fields_get()
    old_record = self.read()
    new_values = {}
    for field in model_fields.keys():
        if field in ignore_fields:
            continue
        if field in vals.keys():
            get_name = fields_mapped.get(field, False)
            if model_fields[field]['type'] == 'many2one':
                old_result = old_record[0][field][1] if old_record[0][field] else ''
                new_result = self.user_id.search([('id', '=', vals[field])]).name if vals[field] else ''
                new_values[field] = {'name': model_fields[field]['string'], 'old': old_result, 'new': new_result,
                                     'display_info': _create_tracking_info(model_fields[field]['string'],
                                                                           old_result, new_result)}
            elif model_fields[field]['type'] == 'many2many':
                """
                    多对多字段目前用的最多的就是[[6,0,ids]]的方式修改,关联记录
                """
                if vals[field][0][0] == 6:
                    old_list = self.env[model_fields[field]['relation']].sudo().search(
                        [('id', 'in', old_record[0][field])]).mapped(
                        get_name if get_name else 'id') if old_record[0][field] else ['']
                    new_list = self.env[model_fields[field]['relation']].sudo().search(
                        [('id', 'in', vals[field][0][2])]).mapped(
                        get_name if get_name else 'id') if vals[field][0][2] else ['']
                    old_result = ', '.join(old_list)
                    new_result = ', '.join(new_list)
                    new_values[field] = {'name': model_fields[field]['string'], 'old': old_result, 'new': new_result,
                                         'display_info': _create_tracking_info(model_fields[field]['string'],
                                                                               old_result, new_result)}
            # elif model_fields[field]['type'] == 'one2many':
            #     """
            #         一对多字段的增删改进行判断处理
            #         {'approval_item_ids': [[4, 9, False], [4, 2, False], [4, 3, False], [4, 4, False], [2, 10, False]]}
            #         {'approval_item_ids': [[4, 9, False], [4, 2, False], [1, 3, {'group_ids': [[6, False, []]]}], [1, 4, {'group_ids': [[6, False, [11, 14, 12]]]}]]}
            #         {'approval_item_ids': [[4, 9, False], [4, 2, False], [4, 3, False], [4, 4, False], [0, 'virtual_185', {'sequence': 1, 'role': '起草', 'group_ids': [[6, False, [14, 13]]], 'user_ids': [[6, False, [2]]]}]]}
            #     """
            #     for one_rec in vals[field]:
            #         if one_rec[0] == 0:
            #             new_result = one_rec[2]
            #             new_values[field] = {'name': model_fields[field]['string'], 'old': old_result,
            #                                  'new': new_result,
            #                                  'display_info': _create_tracking_info(model_fields[field]['string'],
            #                                                                        old_result, new_result)}


            elif model_fields[field]['type'] in ['datetime', 'date']:
                tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
                old_result = old_record[0][field].astimezone(tz) if old_record[0][field] else ''
                new_result = vals[field].astimezone(tz) if vals[field] else ''
                new_values[field] = {'name': model_fields[field]['string'], 'old': old_result, 'new': new_result,
                                     'display_info': _create_tracking_info(model_fields[field]['string'],
                                                                           old_result, new_result)}
            else:
                old_result = old_record[0][field] if old_record[0][field] else ''
                new_result = vals[field] if vals[field] else ''
                new_values[field] = {'name': model_fields[field]['string'], 'old': old_result, 'new': new_result,
                                     'display_info': _create_tracking_info(model_fields[field]['string'], old_result,
                                                                           new_result)}

    r_tracking = '<span> {} has been Changed: {}</span><ul class="o_mail_thread_message_tracking">'.format(tracking_title,
        self.display_name)
    for field in new_values.keys():
        r_tracking += new_values[field]['display_info']
    r_tracking += '</ul>'
    return r_tracking

# liaoziyang 202505211710 在底层model父类添加一个锚点sx方法，为了能让继承的子类模型拥有该方法，以便执行sx模拟页面刷新，触发表单或列表的数据刷新
def sx(self):
    return True
