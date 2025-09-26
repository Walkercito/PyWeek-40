#version 120

// Input vertex attributes (from vertex shader)
varying vec3 fragPosition;
varying vec2 fragTexCoord;
varying vec4 fragColor;
varying vec3 fragNormal;

// Input uniform values
uniform sampler2D texture0;
uniform vec4 colDiffuse;
uniform vec3 viewPos;

// Light definitions
#define MAX_LIGHTS 4
#define LIGHT_DIRECTIONAL 0
#define LIGHT_POINT 1

struct Light {
    int enabled;
    int type;
    vec3 position;
    vec3 target;
    vec4 color;
};

// Input lighting values
uniform Light lights[MAX_LIGHTS];
uniform vec4 ambient;

// Fog parameters for atmospheric perspective on distant buildings
uniform float fogDensity;
uniform vec3 fogColor;

void main()
{
    // Texel color fetching from texture sampler
    vec4 texelColor = texture2D(texture0, fragTexCoord);
    vec3 lightDot = vec3(0.0);
    vec3 normal = normalize(fragNormal);
    vec3 viewD = normalize(viewPos - fragPosition);
    vec3 specular = vec3(0.0);
    
    // Calculate distance-based fog for atmospheric perspective
    float distanceToCamera = length(fragPosition - viewPos);
    float fogFactor = exp(-fogDensity * distanceToCamera * 0.0008);
    fogFactor = clamp(fogFactor, 0.0, 1.0);
    
    // Calculate lighting
    for (int i = 0; i < MAX_LIGHTS; i++)
    {
        if (lights[i].enabled == 1)
        {
            vec3 light = vec3(0.0);
            
            if (lights[i].type == LIGHT_DIRECTIONAL)
            {
                light = -normalize(lights[i].target - lights[i].position);
            }
            
            if (lights[i].type == LIGHT_POINT)
            {
                light = normalize(lights[i].position - fragPosition);
            }
            
            float NdotL = max(dot(normal, light), 0.0);
            lightDot += lights[i].color.rgb * NdotL;
            
            // Enhanced specular for building materials
            float specCo = 0.0;
            if (NdotL > 0.0) {
                vec3 halfDir = normalize(light + viewD);
                specCo = pow(max(0.0, dot(normal, halfDir)), 32.0); // Higher shininess for buildings
            }
            specular += specCo * 0.3; // Moderate specular for building surfaces
        }
    }
    
    // Combine lighting
    vec4 tint = colDiffuse * fragColor;
    vec4 finalColor = texelColor * tint * vec4(lightDot, 1.0);
    finalColor.rgb += specular;
    
    // Add ambient lighting
    finalColor += texelColor * tint * (ambient * 0.3);
    
    // Apply atmospheric fog
    finalColor.rgb = mix(fogColor, finalColor.rgb, fogFactor);
    
    // Gamma correction
    gl_FragColor = pow(finalColor, vec4(1.0/2.2));
}