package com.lowlevellogic.cast.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.lowlevellogic.cast.ui.screens.QueueScreen
import com.lowlevellogic.cast.ui.screens.SettingsScreen
import com.lowlevellogic.cast.ui.screens.StatsScreen

sealed class Screen(val route: String, val label: String, val icon: ImageVector) {
    object Stats : Screen("stats", "Stats", Icons.Default.Star)
    object Queue : Screen("queue", "Queue", Icons.Default.List)
    object Settings : Screen("settings", "Settings", Icons.Default.Settings)
}

val screens = listOf(Screen.Stats, Screen.Queue, Screen.Settings)

@Composable
fun CastNavGraph() {
    val navController = rememberNavController()
    val backStack by navController.currentBackStackEntryAsState()
    val current = backStack?.destination?.route

    Scaffold(
        bottomBar = {
            NavigationBar {
                screens.forEach { screen ->
                    NavigationBarItem(
                        selected = current == screen.route,
                        onClick = {
                            navController.navigate(screen.route) {
                                popUpTo(navController.graph.findStartDestination().id) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(screen.icon, contentDescription = screen.label) },
                        label = { Text(screen.label) },
                    )
                }
            }
        }
    ) { padding ->
        NavHost(navController, startDestination = Screen.Stats.route,
            androidx.compose.ui.Modifier.padding(padding)) {
            composable(Screen.Stats.route) { StatsScreen() }
            composable(Screen.Queue.route) { QueueScreen() }
            composable(Screen.Settings.route) { SettingsScreen() }
        }
    }
}
