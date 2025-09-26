#version 120

// Input vertex attributes
attribute vec3 vertexPosition;
attribute vec2 vertexTexCoord;
attribute vec3 vertexNormal;
attribute vec4 vertexColor;
attribute mat4 instanceTransform;

// Input uniform values
uniform mat4 mvp;
uniform mat4 matModel;
uniform mat4 matView;
uniform mat4 matProjection;
uniform mat4 matNormal;

// Output vertex attributes (to fragment shader)
varying vec3 fragPosition;
varying vec2 fragTexCoord;
varying vec4 fragColor;
varying vec3 fragNormal;

void main()
{
    // Compute model-view-projection matrix for current instance
    mat4 mvpi = mvp * instanceTransform;
    
    // Transform position to world space using instance transform
    vec4 worldPosition = instanceTransform * vec4(vertexPosition, 1.0);
    fragPosition = worldPosition.xyz;
    
    // Pass through texture coordinates and color
    fragTexCoord = vertexTexCoord;
    fragColor = vertexColor;
    
    // Transform normal to world space
    fragNormal = normalize(vec3(instanceTransform * vec4(vertexNormal, 0.0)));
    
    // Calculate final vertex position
    gl_Position = mvpi * vec4(vertexPosition, 1.0);
}