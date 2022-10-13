odoo.define('website_training.trainers', function (require) {
"use strict";


var ajax = require('web.ajax');
ajax.jsonRpc("/modulo_matriculas/ciclos", 'call', {'id': 1}).then(function(data) {
    if (data) {
        console.log(data);
    } else {
       console.log("no");
}});
})