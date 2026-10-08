package com.yourname.helmx

import android.util.Log
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.Query
import kotlinx.coroutines.tasks.await

/** Reads and writes the signed-in user's rides at users/{uid}/rides. */
class RideRepository {

    private val auth = FirebaseAuth.getInstance()
    private val firestore = FirebaseFirestore.getInstance()

    private fun ridesCollection(uid: String? = auth.currentUser?.uid) = uid?.let {
        firestore.collection("users").document(it).collection("rides")
    }

    /**
     * Saves a ride. Not awaited: Firestore queues the write locally and syncs it when online,
     * so the ride is kept even if the screen closes right after STOP.
     */
    fun saveRide(ride: Ride, uid: String?, onFailure: (Exception) -> Unit = {}): Boolean {
        val collection = ridesCollection(uid) ?: return false
        collection.add(ride).addOnFailureListener { e ->
            Log.e("RideRepository", "Saving ride failed", e)
            onFailure(e)
        }
        return true
    }

    suspend fun getRecentRides(limit: Long = 20): Result<List<Ride>> = runCatching {
        val collection = ridesCollection() ?: throw IllegalStateException("Not logged in")
        collection.orderBy("startedAt", Query.Direction.DESCENDING)
            .limit(limit)
            .get()
            .await()
            .documents
            .mapNotNull { doc -> doc.toObject(Ride::class.java)?.copy(id = doc.id) }
    }

    suspend fun getRidesSince(sinceMillis: Long): Result<List<Ride>> = runCatching {
        val collection = ridesCollection() ?: throw IllegalStateException("Not logged in")
        collection.whereGreaterThanOrEqualTo("startedAt", sinceMillis)
            .get()
            .await()
            .documents
            .mapNotNull { doc -> doc.toObject(Ride::class.java)?.copy(id = doc.id) }
    }
}
