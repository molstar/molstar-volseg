
import * as MS from '../molstar-lib-imports';
import PD = MS.ParamDefinition;

import { Choice } from '../choice';


export const DEFAULT_MESH_SERVER = 'http://localhost:9000/v1';


export class MeshServerInfo extends MS.PluginStateObject.Create<MeshServerInfo.Data>({ name: 'Volume Server', typeClass: 'Object' }) { }

export namespace MeshServerInfo {
    export const MeshSourceChoice = new Choice({ empiar: 'EMPIAR', emdb: 'EMDB' }, 'empiar');
    export type MeshSource = Choice.Values<typeof MeshSourceChoice>;

    export const Params = {
        serverUrl: PD.Text(DEFAULT_MESH_SERVER),
        entryId: PD.Text(''),
        source: MeshSourceChoice.PDSelect(),
        // segmentFrom: PD.Numeric(0), // DEBUG
        // segmentTo: PD.Numeric(1_000_000), // DEBUG
    };
    export type Data = PD.Values<typeof Params>;
}
