package com.yourname.helmx

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Filter
import com.yourname.helmx.databinding.ItemPlaceSuggestionBinding

/**
 * Drop-down rows for the search bar. Results come from the geocoder already matched to the
 * query, so the adapter's filter passes everything through instead of prefix-matching.
 */
class PlaceSuggestionAdapter(context: Context) :
    ArrayAdapter<PlaceSuggestion>(context, R.layout.item_place_suggestion) {

    private var items: List<PlaceSuggestion> = emptyList()

    fun setItems(newItems: List<PlaceSuggestion>) {
        items = newItems
        clear()
        addAll(newItems)
        notifyDataSetChanged()
    }

    override fun getView(position: Int, convertView: View?, parent: ViewGroup): View {
        val binding = convertView?.let { ItemPlaceSuggestionBinding.bind(it) }
            ?: ItemPlaceSuggestionBinding.inflate(LayoutInflater.from(context), parent, false)
        val item = getItem(position)
        binding.tvPlaceName.text = item?.name
        binding.tvPlaceAddress.text = item?.address
        binding.tvPlaceAddress.visibility = if (item?.address.isNullOrBlank()) View.GONE else View.VISIBLE
        binding.ivPlaceIcon.setImageResource(if (item?.isRecent == true) R.drawable.ic_history else R.drawable.ic_place_pin)
        return binding.root
    }

    override fun getFilter(): Filter = object : Filter() {
        override fun performFiltering(constraint: CharSequence?) = FilterResults().apply {
            values = items
            count = items.size
        }

        override fun publishResults(constraint: CharSequence?, results: FilterResults?) {
            if ((results?.count ?: 0) > 0) notifyDataSetChanged() else notifyDataSetInvalidated()
        }

        // Selecting a row puts the place name (not the data class toString) in the box
        override fun convertResultToString(resultValue: Any?) = (resultValue as? PlaceSuggestion)?.name ?: ""
    }
}
