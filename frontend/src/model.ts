import { createPluginUI } from 'molstar/lib/mol-plugin-ui/react18';
import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { DefaultPluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';
import { PluginConfig } from 'molstar/lib/mol-plugin/config';
import { StateObjectSelector, StateTransformer } from 'molstar/lib/mol-state';
import { PluginStateObject } from 'molstar/lib/mol-plugin-state/objects';
import { StateTransforms } from 'molstar/lib/mol-plugin-state/transforms';
import { createVolumeRepresentationParams } from 'molstar/lib/mol-plugin-state/helpers/volume-representation-params';
import { Volume } from 'molstar/lib/mol-model/volume';
import { Color } from 'molstar/lib/mol-util/color';
import { ParamDefinition as PD } from 'molstar/lib/mol-util/param-definition';
import { CustomProperties } from 'molstar/lib/mol-model/custom-property';
import { arrayMean, arrayRms } from 'molstar/lib/mol-util/array';
import { Vec2 } from 'molstar/lib/mol-math/linear-algebra';

export class AppModel {
    plugin: PluginUIContext = void 0 as any;

    async init(target: HTMLElement) {
        const defaultSpec = DefaultPluginUISpec();
        this.plugin = await createPluginUI(target, {
            ...defaultSpec,
            layout: {
                initial: {
                    isExpanded: false,
                    showControls: false
                },
            },
            components: {
                controls: { left: 'none', right: 'none', top: 'none', bottom: 'none' },
            },
            canvas3d: {
                camera: {
                    helper: { axes: { name: 'off', params: {} } }
                }
            },
            config: [
                [PluginConfig.Viewport.ShowExpand, false],
                [PluginConfig.Viewport.ShowControls, false],
                [PluginConfig.Viewport.ShowSelectionMode, false],
                [PluginConfig.Viewport.ShowAnimation, false],
            ],
        });

        setTimeout(() => this.load(), 50);
    }

    createSegment(volume: Volume, level: number): Volume {
        console.log(level);
        const { mean, sigma } = volume.grid.stats;
        const { data, space } = volume.grid.cells;
        const newData = new Float32Array(data.length);

        for (let i = 0; i < space.dimensions[0]; i++) {
            if (Math.floor(10 * i / space.dimensions[0]) !== level) continue;

            for (let j = 0; j < space.dimensions[1]; j++) {
                for (let k = 0; k < space.dimensions[2]; k++) {
                    const o = space.dataOffset(i, j, k);
                    const v = (data[o] - mean) / sigma;
                    if (v > 2.5) newData[o] = 1;
                }
            }   
        }

        // for (let i = 0; i < newData.length; i++) {
        //     const v = Math.floor((data[i] - mean) / sigma) === level ? 1 : 0;
        //     newData[i] = v;
        // }

        return {
            sourceData: { kind: 'custom', name: 'test', data: newData as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                ...volume.grid,
                stats: { min: 0, max: 1, mean: arrayMean(newData), sigma: arrayRms(newData) },
                cells: {
                    ...volume.grid.cells,
                    data: newData as any,
                }
            }
        };
    }

    private volume: Volume = undefined as any;
    private currentLevel: any = undefined;

    async showLevel(level: number) {
        const volume = this.createSegment(this.volume, level);

        const update = this.plugin.build();

        if (this.currentLevel) {
            update.delete(this.currentLevel);
        }

        const root = update.toRoot().apply(CreateVolume, { volume });
        this.currentLevel = root.selector;

        // root.apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volume, {
        //     type: 'isosurface',
        //     typeParams: { alpha: 1, isoValue: Volume.IsoValue.absolute(0.5) },
        //     color: 'uniform',
        //     colorParams: { value: Color(Math.round(Math.random() * 0xffffff)) }
        // }));

        const controlPoints: Vec2[] = [
            Vec2.create(0, 0),
            Vec2.create(0.5, 0),
            Vec2.create(0.98, 1),
            Vec2.create(1.1, 1),
        ]

        // const list = {
        //     kind: 'interpolate' as const,
        //     colors: [
        //         [Color(0x0), 0]
        //     ]
        // }

        root.apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volume, {
            type: 'direct-volume',
            typeParams: { 
                ignoreLight: true,
                stepsPerCell: 2,
                controlPoints,
            },
            color: 'uniform',
            colorParams: { value: Color(Math.round(Math.random() * 0xffffff)) }
        }));

        await update.commit();
    }

    async load() {
        const entryId = 'emd-1832';
        const isoLevel = 2.73;
        const url = `https://maps.rcsb.org/em/${entryId}/cell?detail=6`;
        const { plugin } = this;

        const data = await plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: true } });
        const parsed = await plugin.dataFormats.get('dscif')!.parse(plugin, data, { entryId });
        const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
        const volumeData = volume.cell!.obj!.data;
        this.volume = volumeData;

        const repr = plugin.build();

        repr
            .to(volume)
            .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                type: 'isosurface',
                typeParams: { alpha: 0.2, isoValue: Volume.adjustedIsoValue(volumeData, isoLevel, 'relative') },
                color: 'uniform',
                colorParams: { value: Color(0x121212) }
            }));

        await repr.commit();
    }
}


const CreateTransformer = StateTransformer.builderFactory('cellstar');

const CreateVolume = CreateTransformer({
    name: 'create-transformer',
    from: PluginStateObject.Root,
    to: PluginStateObject.Volume.Data,
    params: {
        volume: PD.Value<Volume>(undefined as any, { isHidden: true }),
    }
})({
    apply({ params }) {
        return new PluginStateObject.Volume.Data(params.volume);
    }
})