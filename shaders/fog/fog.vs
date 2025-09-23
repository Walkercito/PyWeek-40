#version 330

in vec3 vertexPosition;
in vec2 vertexTexCoord;
in vec3 vertexNormal;

uniform mat4 mvp;
uniform mat4 matModel;
uniform mat4 matView;
uniform mat4 matProjection;

out vec3 fragPosition;
out vec2 fragTexCoord;
out vec3 fragNormal;

void main()
{
    fragPosition = vec3(matModel * vec4(vertexPosition, 1.0));
    
    fragTexCoord = vertexTexCoord;
    
    fragNormal = normalize(vec3(matModel * vec4(vertexNormal, 0.0)));
    
    gl_Position = mvp * vec4(vertexPosition, 1.0);
}