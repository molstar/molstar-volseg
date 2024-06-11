/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

import { DataFormatProvider } from 'molstar/lib/mol-plugin-state/formats/provider';
import { PluginBehavior } from 'molstar/lib/mol-plugin/behavior';
import { ParamDefinition } from 'molstar/lib/mol-util/param-definition';
import { CVSXFormatProvider } from './formats';

/** Collection of things that can be register/unregistered in a plugin */
interface Registrables {
    dataFormats?: { name: string, provider: DataFormatProvider }[],
}

export const CVSXSpec = PluginBehavior.create<{ autoAttach: boolean }>({
    name: 'CVSXSpec',
    category: 'misc',
    display: {
        name: 'CVSXSpec',
        description: 'CVSXSpec extension',
    },
    ctor: class extends PluginBehavior.Handler<{ autoAttach: boolean }> {
        private readonly registrables: Registrables = {
            dataFormats: [
                { name: 'CVSX', provider: CVSXFormatProvider }
            ],
        };

        register(): void {
            for (const format of this.registrables.dataFormats ?? []) {
                this.ctx.dataFormats.add(format.name, format.provider);
            }
        }
        update(p: { autoAttach: boolean }) {
            const updated = this.params.autoAttach !== p.autoAttach;
            this.params.autoAttach = p.autoAttach;
            return updated;
        }
        unregister() {
            for (const format of this.registrables.dataFormats ?? []) {
                this.ctx.dataFormats.remove(format.name);
            }
        }
    },
    params: () => ({
        autoAttach: ParamDefinition.Boolean(false),
    })
});