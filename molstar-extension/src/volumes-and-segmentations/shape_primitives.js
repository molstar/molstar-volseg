"use strict";
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports._get_target_segment_color = exports.CreateShapePrimitiveProvider = exports.CreateShapePrimitiveProviderParams = exports.isShapePrimitiveParamsValues = exports.Cone = exports.VolsegGeometricSegmentation = exports.VolsegShapePrimitivesData = void 0;
const objects_1 = require("molstar/lib/mol-plugin-state/objects");
const param_definition_1 = require("molstar/lib/mol-util/param-definition");
const mesh_1 = require("molstar/lib/mol-geo/geometry/mesh/mesh");
const mesh_builder_1 = require("molstar/lib/mol-geo/geometry/mesh/mesh-builder");
const sphere_1 = require("molstar/lib/mol-geo/geometry/mesh/builder/sphere");
const linear_algebra_1 = require("molstar/lib/mol-math/linear-algebra");
const shape_1 = require("molstar/lib/mol-model/shape");
const color_1 = require("molstar/lib/mol-util/color");
const mol_state_1 = require("molstar/lib/mol-state");
const cylinder_1 = require("molstar/lib/mol-geo/geometry/mesh/builder/cylinder");
const box_1 = require("molstar/lib/mol-geo/primitive/box");
const pyramid_1 = require("molstar/lib/mol-geo/primitive/pyramid");
const polygon_1 = require("molstar/lib/mol-geo/primitive/polygon");
const ellipsoid_1 = require("molstar/lib/mol-geo/geometry/mesh/builder/ellipsoid");
class VolsegShapePrimitivesData {
    constructor(shapePrimitiveData) {
        this.shapePrimitiveData = shapePrimitiveData;
    }
}
exports.VolsegShapePrimitivesData = VolsegShapePrimitivesData;
class VolsegGeometricSegmentation extends objects_1.PluginStateObject.Create({ name: 'Vol & Seg Geometric Segmentation', typeClass: 'Data' }) {
}
exports.VolsegGeometricSegmentation = VolsegGeometricSegmentation;
let cone;
function Cone() {
    if (!cone)
        cone = (0, pyramid_1.Pyramid)((0, polygon_1.polygon)(48, true));
    return cone;
}
exports.Cone = Cone;
function addBox(state, translation = linear_algebra_1.Vec3.create(0.5, 0.5, 0.5), scaling = linear_algebra_1.Vec3.create(1, 1, 1)) {
    const mat4 = linear_algebra_1.Mat4.identity();
    linear_algebra_1.Mat4.scale(mat4, mat4, scaling);
    linear_algebra_1.Mat4.translate(mat4, mat4, translation);
    mesh_builder_1.MeshBuilder.addPrimitive(state, mat4, (0, box_1.Box)());
}
function addTriangularPyramid(state, translation = linear_algebra_1.Vec3.create(0.5, 0.5, 0.5), scaling = linear_algebra_1.Vec3.create(1, 1, 1)) {
    const mat4 = linear_algebra_1.Mat4.identity();
    linear_algebra_1.Mat4.scale(mat4, mat4, scaling);
    linear_algebra_1.Mat4.translate(mat4, mat4, translation);
    mesh_builder_1.MeshBuilder.addPrimitive(state, mat4, (0, pyramid_1.TriangularPyramid)());
}
const isShapePrimitiveParamsValues = (value) => !!(value === null || value === void 0 ? void 0 : value.segmentAnnotations);
exports.isShapePrimitiveParamsValues = isShapePrimitiveParamsValues;
exports.CreateShapePrimitiveProviderParams = {
    segmentAnnotations: param_definition_1.ParamDefinition.Value([], { isHidden: true }),
    descriptions: param_definition_1.ParamDefinition.Value([], { isHidden: true }),
    segmentationId: param_definition_1.ParamDefinition.Text(''),
    segmentId: param_definition_1.ParamDefinition.Numeric(0),
};
const Transform = mol_state_1.StateTransformer.builderFactory('msvolseg');
exports.CreateShapePrimitiveProvider = Transform({
    name: 'create-shape-primitive-provider',
    display: { name: 'Shape Primitives' },
    from: VolsegGeometricSegmentation,
    to: objects_1.PluginStateObject.Shape.Provider,
    params: exports.CreateShapePrimitiveProviderParams
})({
    apply({ a, params }) {
        return new objects_1.PluginStateObject.Shape.Provider({
            label: 'Shape Primitives',
            data: params,
            // data: params.data,
            params: mesh_1.Mesh.Params,
            geometryUtils: mesh_1.Mesh.Utils,
            getShape: (_, data) => createShapePrimitive(a.data.shapePrimitiveData, params)
        }, { label: 'Shape Primitives' });
    }
});
function _get_target_segment_name(allDescriptions, segment_id) {
    // NOTE: for now single description
    const description = allDescriptions.filter(d => d.target_id && d.target_id.segment_id === segment_id);
    return description[0].name;
}
function _get_target_segment_color(allSegmentAnnotations, segment_id) {
    var _a;
    // NOTE: for now single annotation, should be single one
    const annotation = allSegmentAnnotations.find(a => a.segment_id === segment_id);
    const color = (_a = annotation === null || annotation === void 0 ? void 0 : annotation.color) !== null && _a !== void 0 ? _a : [0.9, 0.9, 0.9, 1.0];
    return color;
}
exports._get_target_segment_color = _get_target_segment_color;
function createShapePrimitive(data, params) {
    const builder = mesh_builder_1.MeshBuilder.createState(512, 512);
    const descriptions = params.descriptions;
    const segmentAnnotations = params.segmentAnnotations;
    const p = data.shape_primitive_list.find(s => s.id === params.segmentId);
    builder.currentGroup = 0;
    switch (p.kind) {
        case 'sphere':
            (0, sphere_1.addSphere)(builder, p.center, p.radius, 2);
            break;
        case 'cylinder':
            (0, cylinder_1.addCylinder)(builder, p.start, p.end, 1, {
                radiusTop: p.radius_top,
                radiusBottom: p.radius_bottom,
                bottomCap: true,
                topCap: true,
            });
            break;
        case 'box':
            addBox(builder, p.translation, p.scaling);
            break;
        case 'pyramid':
            addTriangularPyramid(builder, p.translation, p.scaling);
            break;
        case 'ellipsoid':
            (0, ellipsoid_1.addEllipsoid)(builder, p.center, p.dir_major, p.dir_minor, p.radius_scale, 2);
            break;
    }
    // }
    return shape_1.Shape.create('Shape Primitives', params, mesh_builder_1.MeshBuilder.getMesh(builder), g => color_1.Color.fromNormalizedArray(_get_target_segment_color(segmentAnnotations, p.id), 0), () => 1, g => _get_target_segment_name(descriptions, p.id));
}
