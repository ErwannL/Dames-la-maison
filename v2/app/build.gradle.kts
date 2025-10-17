
plugins {
    alias(libs.plugins.android.application)
}

android {
    namespace = "com.example.damemaison"
    compileSdk 34  // ⬅️ Corrigé cette ligne

    defaultConfig {
        applicationId = "com.example.damemaison"
        minSdk = 21
        targetSdk = 34  // ⬅️ Augmente la version
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            // ⬇️ SUPPRIME la configuration de signature pour l'instant
            signingConfig signingConfigs.debug
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
        
        debug {
            signingConfig signingConfigs.debug
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}

dependencies {
    implementation(libs.appcompat)
    implementation(libs.material)
    implementation(libs.activity)
    implementation(libs.constraintlayout)
    testImplementation(libs.junit)
    androidTestImplementation(libs.ext.junit)
    androidTestImplementation(libs.espresso.core)
}
