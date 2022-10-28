
import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui/react18';
import { DefaultPluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';
import { PluginConfig } from 'molstar/lib/mol-plugin/config';
import { BehaviorSubject } from 'rxjs';

import { Annotation, Segment } from '../volume-api-client-lib/data';
import { VolumeApiV2 } from '../volume-api-client-lib/volume-api';
import { Debugging, ExampleType, splitEntryId, UrlFragmentInfo } from './helpers';
import { Session } from './session';


export const API2 = new VolumeApiV2();

const DEFAULT_EXAMPLE: ExampleType = 'auto';


export class AppModel {
    public exampleType = new BehaviorSubject<ExampleType | undefined>(undefined);
    public entryId = new BehaviorSubject<string>('');
    public status = new BehaviorSubject<'ready' | 'loading' | 'error'>('ready');
    public error = new BehaviorSubject<any>(undefined);

    public annotation = new BehaviorSubject<Annotation | undefined>(undefined);
    public currentSegment = new BehaviorSubject<Segment | undefined>(undefined);
    public pdbs = new BehaviorSubject<string[]>([]);
    public currentPdb = new BehaviorSubject<string | undefined>(undefined);

    public session?: Session;
    private plugin: PluginUIContext = undefined as any;

    async init(target: HTMLElement) {
        const defaultSpec = DefaultPluginUISpec();
        this.plugin = await createPluginUI(target, {
            ...defaultSpec,
            layout: {
                initial: {
                    isExpanded: false,
                    showControls: true,  // original: false
                    controlsDisplay: 'landscape',  // original: not given
                },
            },
            components: {
                // controls: { left: 'none', right: 'none', top: 'none', bottom: 'none' },
                controls: { right: 'none', top: 'none', bottom: 'none' },
            },
            canvas3d: {
                camera: {
                    helper: { axes: { name: 'off', params: {} } }
                }
            },
            config: [
                [PluginConfig.Viewport.ShowExpand, true],  // original: false
                [PluginConfig.Viewport.ShowControls, true],  // original: false
                [PluginConfig.Viewport.ShowSelectionMode, false],
                [PluginConfig.Viewport.ShowAnimation, false],
            ],
        });

        await Debugging.testApiV2(this.plugin, API2);
        // return;

        const fragment = UrlFragmentInfo.get();
        setTimeout(() => this.loadExample(fragment.example ?? DEFAULT_EXAMPLE, fragment.entry), 50);
    }

    /** Reset data */
    private clear() {
        this.error.next(undefined);

        this.annotation.next(undefined);
        this.currentSegment.next(undefined);
        this.pdbs.next([]);
        this.currentPdb.next(undefined);
    }

    async loadExample(exampleType: ExampleType, entryId?: string) {
        this.session = new Session(this, this.plugin);

        const example = this.session.examples[exampleType] ?? this.session.examples[DEFAULT_EXAMPLE];
        entryId ??= example.defaultEntryId;
        console.time(`Load example ${example.exampleType} ${entryId}`);
        const source = splitEntryId(entryId).source as 'empiar' | 'emdb';

        this.clear();
        this.exampleType.next(example.exampleType);
        this.entryId.next(entryId);
        this.status.next('loading');
        UrlFragmentInfo.set({ example: example.exampleType, entry: entryId });

        try {
            await this.plugin.clear();
            this.plugin.behaviors.layout.leftPanelTabName.next('data');
            this.session.metadata = await API2.getMetadata(source, entryId);
            this.annotation.next(this.session.metadata.annotation);
            await example.action(entryId);
            this.status.next('ready');
        } catch (error) {
            this.error.next(error);
            this.status.next('error');
            throw error;
        } finally {
            console.timeEnd(`Load example ${example.exampleType} ${entryId}`);
        }
    }
}

// interface Sessions {
//     current: string,
// }
// namespace Sessions {
//     function create(): Sessions {
//         return { current: UUID.createv4() };
//     }
//     function startSession(sessions: Sessions) {
//         sessions.current = UUID.createv4();
//     }
// }
// class BehaviorSubjectX<T> extends BehaviorSubject<T> {
//     constructor(value: T) {
//         super(value);
//     }
//     next(value: T) {
//         super.next(value);
//     }
// }

