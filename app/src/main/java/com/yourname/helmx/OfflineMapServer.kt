package com.yourname.helmx

import android.content.res.AssetManager
import android.net.Uri
import android.webkit.WebResourceResponse
import java.io.IOException

/**
 * Serves the map page and the bundled offline map package (assets/offline) to the WebView
 * under https://helmx.local/, so the map works without internet.
 *
 * A fake https origin is used instead of file:// URLs because the map library loads tiles,
 * fonts and icons with fetch(), which WebViews block for file:// pages.
 */
class OfflineMapServer(private val assets: AssetManager) {

    companion object {
        const val HOST = "helmx.local"
        const val MAP_URL = "https://$HOST/map.html"

        /** Maps a request path to an asset path, or null if it must not be served. */
        fun assetPathFor(path: String?): String? {
            if (path.isNullOrBlank() || path.contains("..") || path.contains('\\')) return null
            val clean = path.trimStart('/')
            if (clean.isEmpty()) return null
            return if (clean == "map.html") clean else "offline/$clean"
        }

        fun mimeTypeFor(path: String): String = when (path.substringAfterLast('.', "").lowercase()) {
            "html" -> "text/html"
            "js" -> "application/javascript"
            "css" -> "text/css"
            "json" -> "application/json"
            "png" -> "image/png"
            "pbf" -> "application/x-protobuf"
            else -> "application/octet-stream"
        }
    }

    /** Returns a response for helmx.local URLs, or null to let the WebView load the URL normally. */
    fun handle(url: Uri): WebResourceResponse? {
        if (url.host != HOST) return null
        val assetPath = assetPathFor(url.path) ?: return notFound()
        return try {
            val stream = assets.open(assetPath)
            WebResourceResponse(mimeTypeFor(assetPath), if (assetPath.endsWith(".pbf")) null else "UTF-8", stream).apply {
                responseHeaders = mapOf("Access-Control-Allow-Origin" to "*", "Cache-Control" to "max-age=86400")
            }
        } catch (e: IOException) {
            // e.g. a tile outside the downloaded area or a font range we didn't bundle
            notFound()
        }
    }

    private fun notFound() = WebResourceResponse(
        "text/plain", "UTF-8", 404, "Not Found", mapOf("Access-Control-Allow-Origin" to "*"), null
    )
}
