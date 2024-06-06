/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

// import { StateTransformer } from '../../mol-state';
import { PluginStateObject } from '../../../mol-plugin-state/objects';
import { ParamDefinition as PD } from '../../../mol-util/param-definition';
import { Mesh } from '../../../mol-geo/geometry/mesh/mesh';
import { MeshBuilder } from '../../../mol-geo/geometry/mesh/mesh-builder';
import { addSphere } from '../../../mol-geo/geometry/mesh/builder/sphere';
import { Mat4, Vec3 } from '../../../mol-math/linear-algebra';
import { Shape } from '../../../mol-model/shape';
import { Color } from '../../../mol-util/color';
import { StateTransformer } from '../../../mol-state';
import { addCylinder } from '../../../mol-geo/geometry/mesh/builder/cylinder';
import { Box } from '../../../mol-geo/primitive/box';
import { Pyramid, TriangularPyramid } from '../../../mol-geo/primitive/pyramid';
import { Primitive } from '../../../mol-geo/primitive/primitive';
import { polygon } from '../../../mol-geo/primitive/polygon';
import { addEllipsoid } from '../../../mol-geo/geometry/mesh/builder/ellipsoid';
import { DescriptionData, SegmentAnnotationData, Cylinder, ShapePrimitiveData, Ellipsoid, PyramidPrimitive, Sphere, BoxPrimitive } from './volseg-api/data';



export class VolsegShapePrimitivesData {
    constructor(public shapePrimitiveData: ShapePrimitiveData) {
    }
}

export class VolsegGeometricSegmentation extends PluginStateObject.Create<VolsegShapePrimitivesData>({ name: 'Vol & Seg Geometric Segmentation', typeClass: 'Data' }) { }


let cone: Primitive;
export function Cone() {
    if (!cone) cone = Pyramid(polygon(48, true));
    return cone;
}


function addBox(state: MeshBuilder.State,
    translation: Vec3 = Vec3.create(0.5, 0.5, 0.5),
    scaling: Vec3 = Vec3.create(1, 1, 1)) {
    const mat4 = Mat4.identity();
    Mat4.scale(mat4, mat4, scaling);
    Mat4.translate(mat4, mat4, translation);

    MeshBuilder.addPrimitive(state, mat4, Box());
}

function addTriangularPyramid(state: MeshBuilder.State,
    translation: Vec3 = Vec3.create(0.5, 0.5, 0.5),
    scaling: Vec3 = Vec3.create(1, 1, 1)) {
    const mat4 = Mat4.identity();
    Mat4.scale(mat4, mat4, scaling);
    Mat4.translate(mat4, mat4, translation);
    MeshBuilder.addPrimitive(state, mat4, TriangularPyramid());
}

export const isShapePrimitiveParamsValues = (value: CreateShapePrimitiveProviderParamsValues): value is CreateShapePrimitiveProviderParamsValues => !!value?.segmentAnnotations;

export type CreateShapePrimitiveProviderParamsValues = PD.Values<typeof CreateShapePrimitiveProviderParams>;
export const CreateShapePrimitiveProviderParams = {
    segmentAnnotations: PD.Value<SegmentAnnotationData[]>([] as any, { isHidden: true }),
    descriptions: PD.Value<DescriptionData[]>([] as any, { isHidden: true }),
    segmentationId: PD.Text(''),
    segmentId: PD.Numeric(0),
};

const Transform = StateTransformer.builderFactory('msvolseg');
export const CreateShapePrimitiveProvider = Transform({
    name: 'create-shape-primitive-provider',
    display: { name: 'Shape Primitives' },
    from: VolsegGeometricSegmentation,
    to: PluginStateObject.Shape.Provider,
    params: CreateShapePrimitiveProviderParams
})({
    apply({ a, params }) {
        return new PluginStateObject.Shape.Provider({
            label: 'Shape Primitives',
            data: params,
            // data: params.data,
            params: Mesh.Params,
            geometryUtils: Mesh.Utils,
            getShape: (_, data) => createShapePrimitive(a.data.shapePrimitiveData, params)
        }, { label: 'Shape Primitives' });
    }
});


function _get_target_segment_name(allDescriptions: DescriptionData[], segment_id: number) {
    // NOTE: for now single description
    const description = allDescriptions.filter(d => d.target_id && d.target_id.segment_id === segment_id);
    return description[0].name!;
}

export function _get_target_segment_color(allSegmentAnnotations: SegmentAnnotationData[], segment_id: number) {
    // NOTE: for now single annotation, should be single one
    const annotation = allSegmentAnnotations.find(a => a.segment_id === segment_id);
    const color = annotation?.color ?? [0.9, 0.9, 0.9, 1.0];
    return color;
}

function createShapePrimitive(data: ShapePrimitiveData, params: CreateShapePrimitiveProviderParamsValues) {
    const builder = MeshBuilder.createState(512, 512);
    const descriptions = params.descriptions;
    const segmentAnnotations = params.segmentAnnotations;
    const p = data.shape_primitive_list.find(s => s.id === params.segmentId);
    builder.currentGroup = 0;
    switch (p!.kind) {
        case 'sphere':
            addSphere(builder, (p as Sphere).center, (p as Sphere).radius, 2);
            break;
        case 'cylinder':
            addCylinder(builder, (p as Cylinder).start as Vec3, (p as Cylinder).end as Vec3, 1, {
                radiusTop: (p as Cylinder).radius_top,
                radiusBottom: (p as Cylinder).radius_bottom,
                bottomCap: true,
                topCap: true,
            });

            break;
        case 'box':
            addBox(
                builder,
                (p as BoxPrimitive).translation as Vec3,
                (p as BoxPrimitive).scaling as Vec3
            );
            break;
        case 'pyramid':
            addTriangularPyramid(
                builder,
                (p as PyramidPrimitive).translation as Vec3,
                (p as PyramidPrimitive).scaling as Vec3
            );
            break;
        case 'ellipsoid':
            addEllipsoid(
                builder,
                (p as Ellipsoid).center as Vec3,
                (p as Ellipsoid).dir_major as Vec3,
                (p as Ellipsoid).dir_minor as Vec3,
                (p as Ellipsoid).radius_scale as Vec3,
                2
            );
            break;
    }
    // }
    return Shape.create(
        'Shape Primitives',
        params,
        MeshBuilder.getMesh(builder),
        g => Color.fromNormalizedArray(_get_target_segment_color(segmentAnnotations, p!.id), 0),
        () => 1,
        g => _get_target_segment_name(descriptions, p!.id)
    );
}