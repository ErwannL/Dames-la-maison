
plugins {
    alias(libs.plugins.android.application)
}

android {
    namespace = "com.example.damemaison"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.example.damemaison"
        minSdk = 21
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        create("release") {
            // Clé de signature automatique pour GitHub Actions
            storeFile = file("release-keystore.jks")
            storePassword = System.getenv("SIGNING_STORE_PASSWORD") ?: "password"
            keyAlias = System.getenv("SIGNING_KEY_ALIAS") ?: "alias"
            keyPassword = System.getenv("SIGNING_KEY_PASSWORD") ?: "password"
        }
    }

    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
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
