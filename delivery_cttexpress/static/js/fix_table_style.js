/** assets/js/fix_table_style.js **/
odoo.define('delivery_cttexpress.fix_table_style', function (require) {
    "use strict";

    const publicWidget = require('web.public.widget');

    publicWidget.registry.FixTableStyle = publicWidget.Widget.extend({
        selector: '.o_field_widget[name="price_rule_ids"]',
        start: function () {
            this._super.apply(this, arguments);
            this._fixTable();
        },
        _fixTable: function () {
            const table = this.el.querySelector('table.o_list_table');
            if (table) {
                table.style.tableLayout = 'auto';
                table.style.width = '100%';
            }
        }
    });

    return publicWidget.registry.FixTableStyle;
});