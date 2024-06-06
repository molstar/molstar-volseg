"use strict";
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.CVSXSpec = void 0;
const behavior_1 = require("molstar/lib/mol-plugin/behavior");
const param_definition_1 = require("molstar/lib/mol-util/param-definition");
const formats_1 = require("./formats");
exports.CVSXSpec = behavior_1.PluginBehavior.create({
    name: 'CVSXSpec',
    category: 'misc',
    display: {
        name: 'CVSXSpec',
        description: 'CVSXSpec extension',
    },
    ctor: class extends behavior_1.PluginBehavior.Handler {
        constructor() {
            super(...arguments);
            this.registrables = {
                dataFormats: [
                    { name: 'CVSX', provider: formats_1.CVSXFormatProvider }
                ],
            };
        }
        register() {
            var _a;
            for (const format of (_a = this.registrables.dataFormats) !== null && _a !== void 0 ? _a : []) {
                this.ctx.dataFormats.add(format.name, format.provider);
            }
        }
        update(p) {
            const updated = this.params.autoAttach !== p.autoAttach;
            this.params.autoAttach = p.autoAttach;
            return updated;
        }
        unregister() {
            var _a;
            for (const format of (_a = this.registrables.dataFormats) !== null && _a !== void 0 ? _a : []) {
                this.ctx.dataFormats.remove(format.name);
            }
        }
    },
    params: () => ({
        autoAttach: param_definition_1.ParamDefinition.Boolean(false),
    })
});
