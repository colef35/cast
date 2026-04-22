package com.lowlevellogic.cast.ui.screens

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lowlevellogic.cast.data.api.CastApi
import com.lowlevellogic.cast.data.models.Stats
import com.lowlevellogic.cast.data.prefs.UserPrefs
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class StatsState {
    object Loading : StatsState()
    data class Ready(val stats: Stats) : StatsState()
    data class Error(val message: String) : StatsState()
}

@HiltViewModel
class StatsViewModel @Inject constructor(
    private val api: CastApi,
    private val prefs: UserPrefs,
) : ViewModel() {

    private val _state = MutableStateFlow<StatsState>(StatsState.Loading)
    val state: StateFlow<StatsState> = _state

    private val _scanning = MutableStateFlow(false)
    val scanning: StateFlow<Boolean> = _scanning

    init { load() }

    fun load() {
        viewModelScope.launch {
            _state.value = StatsState.Loading
            runCatching { api.getStats() }
                .onSuccess { _state.value = StatsState.Ready(it) }
                .onFailure { _state.value = StatsState.Error(it.message ?: "Failed to load stats") }
        }
    }

    fun triggerScan() {
        val productId = prefs.productId
        if (productId.isBlank()) {
            _state.value = StatsState.Error("No product ID set. Add it in Settings.")
            return
        }
        viewModelScope.launch {
            _scanning.value = true
            runCatching { api.scanAll(productId, prefs.userId) }
                .onSuccess { load() }
                .onFailure { _state.value = StatsState.Error("Scan failed: ${it.message}") }
            _scanning.value = false
        }
    }
}
