
import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui/react18';
import { DefaultPluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';
import { PluginConfig } from 'molstar/lib/mol-plugin/config';
import { BehaviorSubject } from 'rxjs';

import { Annotation, Segment } from '../volume-api-client-lib/data';
import { VolumeApiV2 } from '../volume-api-client-lib/volume-api';
import { Debugging, ExampleType, UrlFragmentInfo } from './helpers';
import { Session } from './session';
import { SubjectSessionManager } from './subject-session-manager';


export const API2 = new VolumeApiV2();

const MAX_ENTRIES_IN_LIST = 1000;
const DEFAULT_EXAMPLE: ExampleType = 'auto';


export class AppModel {
    public entryList = new BehaviorSubject<{ [source: string]: string[] }>({});

    private subjectMgr = new SubjectSessionManager();

    public exampleType = this.subjectMgr.behaviorSubject<ExampleType | undefined>(undefined);
    public entryId = this.subjectMgr.behaviorSubject<string>('');
    public status = this.subjectMgr.behaviorSubject<'ready' | 'loading' | 'error'>('ready');
    public error = this.subjectMgr.behaviorSubject<any>(undefined);

    public annotation = this.subjectMgr.behaviorSubject<Annotation | undefined>(undefined);
    public currentSegment = this.subjectMgr.behaviorSubject<Segment | undefined>(undefined);
    public pdbs = this.subjectMgr.behaviorSubject<string[]>([]);
    public currentPdb = this.subjectMgr.behaviorSubject<string | undefined>(undefined);

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

        API2.getEntryList(MAX_ENTRIES_IN_LIST).then(list => this.entryList.next(list));

        // await Debugging.testApiV2(this.plugin, API2);
        // return;

        const fragment = UrlFragmentInfo.get();
        setTimeout(() => this.loadExample(fragment.example ?? DEFAULT_EXAMPLE, fragment.entry), 50); // why setTimeout here?
    }

    async loadExample(exampleType: ExampleType, entryId?: string) {
        const sessionId = this.subjectMgr.startNewSession();
        this.subjectMgr.resetAllSubjects();

        this.session = new Session(sessionId, this, this.plugin);

        const example = this.session.examples[exampleType] ?? this.session.examples[DEFAULT_EXAMPLE];
        entryId ??= example.defaultEntryId;
        console.time(`Load example ${example.exampleType} ${entryId}`);

        this.exampleType.nextWithinSession(example.exampleType, sessionId);
        this.entryId.nextWithinSession(entryId, sessionId);
        this.status.nextWithinSession('loading', sessionId);
        UrlFragmentInfo.set({ example: example.exampleType, entry: entryId });

        try {
            await this.plugin.clear();
            this.plugin.behaviors.layout.leftPanelTabName.next('data');
            await example.action(entryId);
            this.status.nextWithinSession('ready', sessionId);
        } catch (error) {
            this.error.nextWithinSession(error, sessionId);
            this.status.nextWithinSession('error', sessionId);
            throw error;
        } finally {
            console.timeEnd(`Load example ${example.exampleType} ${entryId}`);
        }
    }
}

