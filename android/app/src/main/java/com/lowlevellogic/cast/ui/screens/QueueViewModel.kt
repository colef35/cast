package com.lowlevellogic.cast.ui.screens

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lowlevellogic.cast.data.api.CastApi
import com.lowlevellogic.cast.data.models.Opportunity
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class QueueState {
    object Loading : QueueState()
    data class Ready(val items: List<Opportunity>) : QueueState()
    data class Error(val message: String) : QueueState()
}

@HiltViewModel
class QueueViewModel @Inject constructor(
    private val api: CastApi,
) : ViewModel() {

    private val userId = "TODO_replace_with_real_user_id"

    private val _state = MutableStateFlow<QueueState>(QueueState.Loading)
    val state: StateFlow<QueueState> = _state

    init { load() }

    fun load() {
        viewModelScope.launch {
            _state.value = QueueState.Loading
            runCatching { api.getPending(userId) }
                .onSuccess { _state.value = QueueState.Ready(it) }
                .onFailure { _state.value = QueueState.Error(it.message ?: "Unknown error") }
        }
    }

    fun approve(opp: Opportunity) = act(opp) { api.approve(opp.id, userId) }
    fun reject(opp: Opportunity) = act(opp) { api.reject(opp.id, userId) }

    private fun act(opp: Opportunity, block: suspend () -> Opportunity) {
        viewModelScope.launch {
            runCatching { block() }.onSuccess {
                val current = (_state.value as? QueueState.Ready)?.items ?: return@onSuccess
                _state.value = QueueState.Ready(current.filter { it.id != opp.id })
            }
        }
    }
}
