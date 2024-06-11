/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

import { Vec3 } from 'molstar/lib/mol-math/linear-algebra';
import { Source } from '../../../common';

export interface GeometricSegmentationData {
    segmentation_id: string
    primitives: { [timeframeIndex: number]: ShapePrimitiveData }
}

export interface ShapePrimitiveData {
    shape_primitive_list: Array<BoxPrimitive | Sphere | Cylinder | Ellipsoid | PyramidPrimitive>
}

export interface ShapePrimitiveBase {
    // to be able to refer to it in annotations
    id: number
    kind: ShapePrimitiveKind
}

export type ShapePrimitiveKind = 'sphere' | 'tube' | 'cylinder' | 'box' | 'ellipsoid' | 'pyramid'

export interface RotationParameters {
    axis: Vec3
    radians: number
}

export interface Sphere extends ShapePrimitiveBase {
    // in angstroms
    center: Vec3
    radius: number
}

export interface BoxPrimitive extends ShapePrimitiveBase {
    // with respect to origin 0, 0, 0
    translation: Vec3
    scaling: Vec3
    rotation: RotationParameters
}

export interface Cylinder extends ShapePrimitiveBase {
    start: Vec3
    end: Vec3
    radius_bottom: number
    radius_top: number // =0 <=> cone
}

export interface Ellipsoid extends ShapePrimitiveBase {
    dir_major: Vec3
    dir_minor: Vec3
    center: Vec3
    radius_scale: Vec3
}

export interface PyramidPrimitive extends ShapePrimitiveBase {
    // with respect to origin 0, 0, 0
    translation: Vec3
    scaling: Vec3
    rotation: RotationParameters
}

export type ParsedSegmentKey = {
    kind: 'lattice' | 'mesh' | 'primitive'
    segmentationId: string
    segmentId: number
}

export interface Metadata {
    grid: GridMetadata,
    annotation?: AnnotationMetadata
}

export interface GridMetadata {
    entry_id: EntryId
    volumes: VolumesMetadata
    segmentation_lattices?: SegmentationLatticesMetadata
    segmentation_meshes?: MeshSegmentationSetsMetadata
    geometric_segmentation?: GeometricSegmentationSetsMetadata
}

export interface MeshSegmentationSetsMetadata {
    segmentation_ids: string[]
    segmentation_metadata: { [segmentation_id: string]: MeshesMetadata }
    // maps set ids to time info
    time_info: { [segmentation_id: string]: TimeInfo }
}

export interface MeshesMetadata {
    // maps timeframe index to MeshesTimeframeMetadata with mesh comp num
    mesh_timeframes: { [timeframe_index: number]: MeshComponentNumbers }
    detail_lvl_to_fraction: {
        [lvl: number]: number
    }
}

export interface MeshComponentNumbers {
    segment_ids?: {
        [segId: number]: {
            detail_lvls: {
                [detail: number]: {
                    mesh_ids: {
                        [meshId: number]: {
                            num_triangles: number
                            num_vertices: number
                            num_normals?: number
                        }
                    }
                }
            }
        }
    }
}

export interface GeometricSegmentationSetsMetadata {
    segmentation_ids: string[]
    // maps set ids to time info
    time_info: { [segmentation_id: string]: TimeInfo }
}

export interface VolumesMetadata {
    channel_ids: string[]
    // Values of time dimension
    time_info: TimeInfo
    volume_sampling_info: VolumeSamplingInfo
}

export interface DownsamplingLevelInfo {
    level: number
    available: boolean
}

export interface SamplingInfo {
    // Info about 'downsampling dimension'
    spatial_downsampling_levels: DownsamplingLevelInfo[]
    boxes: { [downsampling: number]: SamplingBox }
    time_transformations: TimeTransformation[]
    // e.g. (0, 1, 2) as standard
    original_axis_order: Vector3
    source_axes_units: { [ axis: string ]: string}
}

export interface VolumeSamplingInfo extends SamplingInfo {
    // resolution -> time -> channel_id
    descriptive_statistics: {
        [resolution: number]: {
            [time: number]: {
                [channel_id: string]: VolumeDescriptiveStatistics
            }
        }
    }
}

export interface VolumeDescriptiveStatistics {
    mean: number
    min: number
    max: number
    std: number
}

export interface TimeTransformation {
    // to which downsampling level it is applied: can be to specific level, can be to all lvls
    downsampling_level: 'all' | number
    factor: number
}

export interface TimeInfo {
    // just one kind - range
    kind: string
    start: number
    end: number
    units: string
}

export interface SamplingBox {
    origin: Vector3
    voxel_size: Vector3
    grid_dimensions: Vector3
}

export interface SegmentationLattices {
    segmentation_lattice_ids: number[],
    segmentation_downsamplings: { [lattice: number]: number[] },
}

export interface SegmentationLatticesMetadata {
    // e.g. label groups (Cell, Chromosomes)
    segmentation_ids: string[]
    segmentation_sampling_info: { [lattice_id: string]: SamplingInfo }
    // maps lattice id to TimeInfo
    time_info: { [segmentation_id: string]: TimeInfo }
}

export interface EntryId {
    source_db_name: Source
    source_db_id: string
}

export interface AnnotationMetadata {
    name?: string
    entry_id: EntryId
    // id => DescriptionData
    descriptions: { [id: string]: DescriptionData }
    segment_annotations: SegmentAnnotationData[]
    details?: string
    volume_channels_annotations?: ChannelAnnotation[]
}

export interface ChannelAnnotation {
    channel_id: string
    color: Vector4
    label?: string
}

export interface DescriptionData {
    id: string
    target_kind: 'lattice' | 'mesh' | 'primitive' | 'entry'
    target_id?: TargetId
    name?: string
    external_references?: ExternalReference[]
    is_hidden?: boolean
    time?: number | number[] | Vector2[]

    details?: DetailsText
    metadata?: { [key: string]: any}
}

export interface TargetId {
    segmentation_id: string
    segment_id: number
}

export interface DetailsText {
    format: 'text' | 'markdown'
    text: string
}



export interface SegmentAnnotationData {
    id: string
    segment_kind: 'lattice' | 'mesh' | 'primitive'
    segment_id: number
    segmentation_id: string
    color?: Vector4
    // NOTE: only a single number or number[] is currently supported
    time?: number | number[] | Vector2[]
}

export interface ExternalReference {
    id: string
    resource?: string
    accession?: string
    label?: string,
    description?: string
    url?: string
}

type Vector2 = [number, number];
type Vector3 = [number, number, number];
export type Vector4 = [number, number, number, number];