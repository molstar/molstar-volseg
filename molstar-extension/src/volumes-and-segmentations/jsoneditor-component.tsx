/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

import React, { useEffect, useRef } from 'react';
import JSONEditor, { JSONEditorOptions } from 'jsoneditor';
import 'jsoneditor/dist/jsoneditor.css';
import { VolsegEntryData } from './entry-root';
import { Button } from '../../../mol-plugin-ui/controls/common';
import { AnnotationMetadata } from './volseg-api/data';

interface JSONEditorComponentProps {
    jsonData: any;
    entryData: VolsegEntryData
}

async function updateJSON(jsonData: AnnotationMetadata, entryData: VolsegEntryData) {
    await entryData.api.updateAnnotationsJson(entryData.source, entryData.entryId, jsonData);
    await entryData.updateMetadata();
}

export const JSONEditorComponent: React.FC<JSONEditorComponentProps> = ({ jsonData, entryData }: { jsonData: AnnotationMetadata, entryData: VolsegEntryData }) => {
    const containerRef = useRef<HTMLDivElement | null>(null);
    let jsonEditor: JSONEditor | null = null;
    const jsonDataUpdated = useRef(jsonData);
    useEffect(() => {
        if (containerRef.current) {
            const options: JSONEditorOptions = {
                onChangeJSON: async (jsonData) => {
                    jsonDataUpdated.current = jsonData;
                }
            };
            jsonEditor = new JSONEditor(containerRef.current, options);
            jsonEditor.set(jsonData);
        }

        return () => {
            if (jsonEditor) {
                jsonEditor.destroy();
            }
        };
    }, [jsonData]);


    return (
        <div style={{ flex: '1', flexDirection: 'column' }}>
            <div ref={containerRef} style={{ width: '100%', height: '400px' }} />
            <Button onClick={async () => await updateJSON(jsonDataUpdated.current, entryData)}>Update annotations.json</Button>
        </div>
    );
};