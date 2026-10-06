"use client"

/**
 * File: contact-form.tsx
 * Purpose: Contact form component with email validation and submission handling
 * Author: GitHub Copilot
 */

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { useToast } from "@/hooks/use-toast"

export function ContactForm() {
  const [isLoading, setIsLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const { toast } = useToast()
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    if (successMessage) {
      setSuccessMessage(null)
    }
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      })

      const result = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(result?.error || "Failed to send your message. Please try again.")
      }

      const userEmailStatus = result?.emailStatus?.user

      toast({
        title: "Success",
        description: "Your message has been sent successfully. We'll get back to you soon!",
      })

      setSuccessMessage(
        userEmailStatus
          ? "Your message was sent successfully and a confirmation email was delivered to your inbox."
          : "Your message was sent successfully. We received it and will get back to you soon."
      )

      setFormData({
        name: "",
        email: "",
        subject: "",
        message: "",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send your message. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {successMessage ? (
        <Alert className="border-primary/40 bg-primary/10 text-foreground">
          <AlertTitle>Message sent</AlertTitle>
          <AlertDescription>{successMessage}</AlertDescription>
        </Alert>
      ) : null}

      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          name="name"
          placeholder="Your name"
          value={formData.name}
          maxLength={100}
          onChange={handleChange}
          required
          className="border-border/50 bg-background/50"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          name="email"
          type="email"
          placeholder="your.email@example.com"
          value={formData.email}
          maxLength={254}
          onChange={handleChange}
          required
          className="border-border/50 bg-background/50"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="subject">Subject</Label>
        <Input
          id="subject"
          name="subject"
          placeholder="What is this about?"
          value={formData.subject}
          maxLength={200}
          onChange={handleChange}
          required
          className="border-border/50 bg-background/50"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="message">Message</Label>
        <Textarea
          id="message"
          name="message"
          placeholder="Tell us more about your inquiry..."
          value={formData.message}
          maxLength={5000}
          onChange={handleChange}
          required
          rows={6}
          className="border-border/50 bg-background/50 resize-none"
        />
      </div>

      <Button
        type="submit"
        disabled={isLoading}
        className="w-full bg-gradient-to-r from-primary to-accent hover:shadow-lg hover:shadow-primary/50"
      >
        {isLoading ? "Sending..." : "Send Message"}
      </Button>
    </form>
  )
}
