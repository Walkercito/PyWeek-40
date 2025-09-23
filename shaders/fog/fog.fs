#version 330

// for deeper understanding of the code, please visit this blog: https://mini.gmshaders.com/p/volume-shadows

in vec3 fragPosition;
in vec2 fragTexCoord;
in vec3 fragNormal;

// uniforms
uniform float time;
uniform vec3 viewPos;
uniform vec4 colDiffuse;

// fog parameters 
uniform float fogDensity = 0.8;
uniform float fogSpeed = 0.5;
uniform float fogScale = 4.0;
uniform float fogHeight = 2.0;
uniform vec3 fogColor = vec3(0.9, 0.95, 1.0);

out vec4 finalColor;

float hash(vec2 p) {
    p = fract(p * vec2(443.8975, 397.2973));
    p += dot(p.xy, p.yx + 19.19);
    return fract(p.x * p.y);
}

float smoothNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
    
    float a = hash(i + vec2(0.0, 0.0));
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float dynamicFBM(vec2 p, float timeOffset) {
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;
    
    float angle = (time + timeOffset) * 0.02; 
    mat2 rotation = mat2(cos(angle), -sin(angle), sin(angle), cos(angle));
    
    for (int i = 0; i < 4; i++) {
        if (i % 3 == 0) p = rotation * p;
        value += amplitude * smoothNoise(p * frequency);
        frequency *= 2.0;
        amplitude *= 0.5;
    }
    
    return value;
}

vec2 swirl(vec2 uv, float strength, float timeScale) {
    vec2 center = vec2(0.5);
    vec2 delta = uv - center;
    float dist = length(delta);
    float angle = atan(delta.y, delta.x) + strength * 0.1 * sin(time * timeScale * 0.2) * (1.0 - dist);
    return center + dist * vec2(cos(angle), sin(angle));
}

float getDynamicFog(vec2 baseUV, vec3 viewDir, float layer) {
    vec2 parallaxOffset = viewDir.xz * layer * 0.15;
    vec2 uv = baseUV + parallaxOffset;
    
    float fastTime = time * fogSpeed * 0.3;    
    float slowTime = time * fogSpeed * 0.1;    
    float mediumTime = time * fogSpeed * 0.2;  
    
    uv = swirl(uv * 0.5 + 0.5, 0.1, 0.2) * 2.0 - 1.0; 
    
    vec2 movement1 = vec2(
        sin(fastTime * 0.2) * 0.1,    
        cos(fastTime * 0.15) * 0.08   
    );
    
    vec2 movement2 = vec2(
        sin(slowTime * 0.3) * 0.15,  
        cos(mediumTime * 0.25) * 0.12 
    );
    
    vec2 movement3 = vec2(
        cos(fastTime * 0.3) * 0.08, 
        sin(mediumTime * 0.4) * 0.1   
    );
    
    float noise1 = dynamicFBM((uv + movement1) * fogScale, 0.0);
    float noise2 = dynamicFBM((uv + movement2) * fogScale * 0.6, 100.0);
    float noise3 = dynamicFBM((uv + movement3) * fogScale * 1.4, 200.0);
    
    float weight1 = 0.5 + 0.1 * sin(time * 0.15);  
    float weight2 = 0.7 + 0.08 * cos(time * 0.2);  
    float weight3 = 0.6 + 0.05 * sin(time * 0.35);  
    
    return (noise1 * weight1 + noise2 * weight2 + noise3 * weight3) / (weight1 + weight2 + weight3);
}

void main()
{
    vec3 viewDir = normalize(fragPosition - viewPos);
    float distanceToCamera = length(fragPosition - viewPos);
    vec2 baseUV = fragPosition.xz * 0.08;
    float heightFactor = exp(-max(0.0, fragPosition.y) / fogHeight);
    float fogLayer1 = getDynamicFog(baseUV, viewDir, 0.0);        // upper fog
    float fogLayer2 = getDynamicFog(baseUV, viewDir, 0.4) * 0.8;  // middle fog
    float fogLayer3 = getDynamicFog(baseUV, viewDir, 0.8) * 0.6;  // lower fog
    float fogLayer4 = getDynamicFog(baseUV, viewDir, 1.2) * 0.4;  // very lower fog
    
    float totalFog = (fogLayer1 + fogLayer2 + fogLayer3 + fogLayer4) / 2.8;
    totalFog = clamp(totalFog, 0.0, 1.0);
    
    totalFog *= heightFactor;
    
    float distanceFactor = 1.0 - exp(-distanceToCamera * 0.03);
    totalFog *= mix(0.2, 1.0, distanceFactor);
    
    float viewAngleFactor = max(0.0, -viewDir.y);
    totalFog += viewAngleFactor * 0.3;
    
    totalFog *= fogDensity;
    
    float colorVariation1 = sin(time * 0.1 + distanceToCamera * 0.05) * 0.05;
    float colorVariation2 = cos(time * 0.08 + fragPosition.x * 0.02) * 0.04;
    
    vec3 baseColor = fogColor;
    vec3 highlightColor = vec3(0.4, 0.7, 1.0);  // light blue
    vec3 shadowColor = vec3(0.2, 0.4, 0.7);     // dark blue

    vec3 finalFogColor = mix(
        mix(shadowColor, baseColor, totalFog),
        highlightColor,
        colorVariation1 + colorVariation2 + 0.1
    );
    
    vec3 violetTint = vec3(0.6, 0.4, 0.8);
    finalFogColor = mix(finalFogColor, violetTint, totalFog * 0.2);

    float alpha = clamp(totalFog, 0.0, 0.9);
    alpha *= 0.9 + 0.1 * sin(time * 0.5);
    
    finalColor = vec4(finalFogColor, alpha);
}