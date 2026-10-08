package com.yourname.helmx

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.yourname.helmx.databinding.ItemRideHistoryBinding
import java.text.DateFormat
import java.util.Date
import java.util.Locale

class RideHistoryAdapter(private var rides: List<Ride> = emptyList()) :
    RecyclerView.Adapter<RideHistoryAdapter.RideViewHolder>() {

    class RideViewHolder(val binding: ItemRideHistoryBinding) :
        RecyclerView.ViewHolder(binding.root)

    private val dateFormat = DateFormat.getDateInstance(DateFormat.MEDIUM)

    fun submitList(newRides: List<Ride>) {
        rides = newRides
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RideViewHolder {
        val binding = ItemRideHistoryBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return RideViewHolder(binding)
    }

    override fun onBindViewHolder(holder: RideViewHolder, position: Int) {
        val ride = rides[position]
        holder.binding.apply {
            tvDestination.text = if (ride.destination.isBlank()) "Ride" else "To: ${ride.destination}"
            tvDate.text = dateFormat.format(Date(ride.startedAt))
            tvDistance.text = String.format(Locale.getDefault(), "%.1f km", ride.distanceKm)
            tvDuration.text = formatDuration(ride.durationSec)
            tvAvgSpeed.text = String.format(Locale.getDefault(), "%.0f km/h", ride.avgSpeedKmh)
        }
    }

    override fun getItemCount() = rides.size

    companion object {
        fun formatDuration(seconds: Long): String {
            val minutes = (seconds + 30) / 60
            return if (minutes < 60) "$minutes min" else "${minutes / 60} h ${minutes % 60} min"
        }
    }
}
