package com.yourname.helmx

import com.google.firebase.firestore.IgnoreExtraProperties

// Older documents may still contain a "password" field; ignore it when deserialising.
@IgnoreExtraProperties
data class User (
    val id: String = "",
    val fullname: String = "",
    val email: String = "",
    val phone: String = "",
    val createdAt: Long = 0L
)
