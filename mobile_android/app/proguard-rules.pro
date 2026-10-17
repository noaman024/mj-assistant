# ProGuard rules for MJ Assistant
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class com.mj.assistant.** { *; }
-keepattributes JavascriptInterface
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
