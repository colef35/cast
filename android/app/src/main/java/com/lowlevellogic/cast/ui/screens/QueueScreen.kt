package com.lowlevellogic.cast.ui.screens

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.lowlevellogic.cast.data.models.Opportunity
import kotlin.math.abs

@Composable
fun QueueScreen(vm: QueueViewModel = hiltViewModel()) {
    val state by vm.state.collectAsState()

    when (val s = state) {
        is QueueState.Loading -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        is QueueState.Error -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(s.message, color = MaterialTheme.colorScheme.error)
                Spacer(Modifier.height(12.dp))
                Button(onClick = vm::load) { Text("Retry") }
            }
        }
        is QueueState.Ready -> {
            if (s.items.isEmpty()) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("All caught up", style = MaterialTheme.typography.titleMedium)
                }
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    items(s.items, key = { it.id }) { opp ->
                        SwipeableOpportunityCard(
                            opp = opp,
                            onApprove = { vm.approve(opp) },
                            onReject = { vm.reject(opp) },
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun SwipeableOpportunityCard(
    opp: Opportunity,
    onApprove: () -> Unit,
    onReject: () -> Unit,
) {
    var offsetX by remember { mutableStateOf(0f) }
    val animatedOffset by animateFloatAsState(targetValue = offsetX, label = "swipe")
    val threshold = 200f

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .pointerInput(Unit) {
                detectHorizontalDragGestures(
                    onDragEnd = {
                        when {
                            offsetX > threshold -> { onApprove(); offsetX = 0f }
                            offsetX < -threshold -> { onReject(); offsetX = 0f }
                            else -> offsetX = 0f
                        }
                    },
                    onHorizontalDrag = { _, delta -> offsetX = (offsetX + delta).coerceIn(-threshold * 1.2f, threshold * 1.2f) }
                )
            }
    ) {
        // Background hint
        Row(
            Modifier.fillMaxWidth().matchParentSize().padding(horizontal = 24.dp),
            horizontalArrangement = if (offsetX > 0) Arrangement.Start else Arrangement.End,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (offsetX > 0) {
                Icon(Icons.Default.Check, contentDescription = "Approve", tint = Color(0xFF4CAF50))
            } else {
                Icon(Icons.Default.Close, contentDescription = "Reject", tint = Color(0xFFF44336))
            }
        }

        OpportunityCard(
            opp = opp,
            modifier = Modifier.offset(x = animatedOffset.dp),
        )
    }
}

@Composable
fun OpportunityCard(opp: Opportunity, modifier: Modifier = Modifier) {
    Card(modifier = modifier.fillMaxWidth(), elevation = CardDefaults.cardElevation(2.dp)) {
        Column(Modifier.padding(16.dp)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    opp.channel.uppercase(),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(
                    "ROI ${(opp.roiScore * 100).toInt()}%",
                    style = MaterialTheme.typography.labelSmall,
                )
            }
            Spacer(Modifier.height(8.dp))
            Text(opp.sourceTitle, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(8.dp))
            opp.draft?.let {
                HorizontalDivider()
                Spacer(Modifier.height(8.dp))
                Text("Draft", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.secondary)
                Spacer(Modifier.height(4.dp))
                Text(it, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}
