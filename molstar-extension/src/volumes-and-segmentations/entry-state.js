"use strict";
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.VOLSEG_STATE_FROM_ENTRY_TRANSFORMER_NAME = exports.VolsegState = exports.VolsegStateParams = exports.VolumeTypeChoice = void 0;
const objects_1 = require("molstar/lib/mol-plugin-state/objects");
const param_choice_1 = require("molstar/lib/mol-util/param-choice");
const color_1 = require("molstar/lib/mol-util/color");
const param_definition_1 = require("molstar/lib/mol-util/param-definition");
exports.VolumeTypeChoice = new param_choice_1.Choice({ 'isosurface': 'Isosurface', 'direct-volume': 'Direct volume', 'slice': 'Slice', 'off': 'Off' }, 'isosurface');
exports.VolsegStateParams = {
    selectedSegment: param_definition_1.ParamDefinition.Text(''),
    visibleSegments: param_definition_1.ParamDefinition.ObjectList({
        segmentKey: param_definition_1.ParamDefinition.Text('')
    }, k => k.segmentKey),
    visibleModels: param_definition_1.ParamDefinition.ObjectList({ pdbId: param_definition_1.ParamDefinition.Text('') }, s => s.pdbId.toString()),
    channelsData: param_definition_1.ParamDefinition.ObjectList({
        channelId: param_definition_1.ParamDefinition.Text('0'),
        volumeIsovalueKind: param_definition_1.ParamDefinition.Select('relative', [['relative', 'Relative'], ['absolute', 'Absolute']]),
        volumeIsovalueValue: param_definition_1.ParamDefinition.Numeric(1),
        volumeType: exports.VolumeTypeChoice.PDSelect(),
        volumeOpacity: param_definition_1.ParamDefinition.Numeric(0.2, { min: 0, max: 1, step: 0.05 }),
        label: param_definition_1.ParamDefinition.Text(''),
        color: param_definition_1.ParamDefinition.Color((0, color_1.Color)(0x121212))
    }, i => i.channelId)
};
class VolsegState extends objects_1.PluginStateObject.Create({ name: 'Vol & Seg Entry State', typeClass: 'Data' }) {
}
exports.VolsegState = VolsegState;
exports.VOLSEG_STATE_FROM_ENTRY_TRANSFORMER_NAME = 'volseg-state-from-entry'; // defined here to avoid cyclic dependency
