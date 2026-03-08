package com.mekatronik.modbussim.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val DarkColors = darkColorScheme(
    primary = BrandBlue,
    onPrimary = TextPrimary,
    primaryContainer = BrandBlueDark,
    secondary = AccentCyan,
    onSecondary = BgDark,
    background = BgDark,
    onBackground = TextPrimary,
    surface = BgPanel,
    onSurface = TextPrimary,
    surfaceVariant = BgCard,
    onSurfaceVariant = TextSecondary,
    error = AccentRed,
    onError = TextPrimary,
    outline = BorderColor,
)

@Composable
fun MekatronikTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColors,
        content = content,
    )
}
