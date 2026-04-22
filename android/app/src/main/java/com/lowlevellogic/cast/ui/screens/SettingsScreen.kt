package com.lowlevellogic.cast.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.lowlevellogic.cast.data.prefs.UserPrefs

@Composable
fun SettingsScreen() {
    val context = LocalContext.current
    val prefs = remember { UserPrefs(context) }

    var apiUrl by remember { mutableStateOf(prefs.apiUrl) }
    var productId by remember { mutableStateOf(prefs.productId) }
    var saved by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Settings", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Black)

        Text("User ID", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Card {
            Text(
                prefs.userId,
                modifier = Modifier.padding(12.dp),
                style = MaterialTheme.typography.bodySmall,
                fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace,
            )
        }

        OutlinedTextField(
            value = productId,
            onValueChange = { productId = it; saved = false },
            label = { Text("Product ID") },
            placeholder = { Text("Paste from seed_product.py output") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )

        OutlinedTextField(
            value = apiUrl,
            onValueChange = { apiUrl = it; saved = false },
            label = { Text("API URL") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
        )

        Button(
            onClick = {
                prefs.productId = productId.trim()
                prefs.apiUrl = apiUrl.trim()
                saved = true
            },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Save")
        }

        if (saved) {
            Text("Saved. Restart the app for API URL changes to take effect.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.primary)
        }
    }
}
