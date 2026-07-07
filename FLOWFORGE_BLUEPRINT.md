# FlowForge Blueprint

## Product Vision

FlowForge is the conversational automation module of the ForgeSphere ecosystem.

It is designed to build business assistants through reusable capabilities, configurable flows, external connectors and client-specific knowledge.

FlowForge is not a single chatbot. It is a modular engine for creating, configuring and deploying automated business conversations across different channels.

---

## Core Principles

1. The engine must be reusable.
2. Clients should be configured, not hardcoded.
3. Capabilities should be enabled or disabled per client.
4. Connectors must be isolated from conversation logic.
5. Actions must be reusable and independent.
6. Knowledge must be separated from application configuration.
7. Each module must have a clear responsibility.

---

## Main Concepts

### Client

A business or project using FlowForge.

Examples:

- Tarot reader
- Restaurant
- Clinic
- Lawyer
- Online shop

### Channel

Where the conversation happens.

Examples:

- WhatsApp
- Web widget
- Telegram
- REST API
- CLI

### Capability

A reusable business function that can be enabled or disabled.

Examples:

- FAQ
- Booking
- Calendar
- Lead capture
- Human transfer
- Analytics
- Payments

### Flow

The conversation path followed by the user.

Examples:

- Booking flow
- FAQ flow
- Sales flow
- Support flow

### Action

An executable operation triggered by a flow.

Examples:

- Create booking
- Send email
- Save lead
- Transfer to human
- Trigger webhook

### Connector

An integration with an external platform or service.

Examples:

- WhatsApp
- Google Calendar
- SMTP
- Stripe
- Telegram

### Knowledge

Business-specific information used by the bot.

Examples:

- Services
- Prices
- FAQs
- Opening hours
- Policies

---

## Target Architecture

```text
Channel
   ↓
Connector / Interface
   ↓
FlowForge Engine
   ↓
Bot / Flow Manager
   ↓
Capability Manager
   ↓
Actions
   ↓
External Connectors
   ↓
Response