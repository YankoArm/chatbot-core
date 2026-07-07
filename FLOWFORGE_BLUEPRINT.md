# FlowForge Blueprint

## Product Vision

FlowForge is the conversational automation framework of the ForgeSphere ecosystem.

Its purpose is to build reusable business assistants through configurable capabilities, conversation flows, external connectors and business-specific knowledge.

FlowForge is not a chatbot.

It is a modular engine designed to create, configure and deploy conversational assistants across multiple communication channels.

Unlike traditional chatbot platforms, FlowForge is designed around collaboration, modularity and conversation continuity rather than rigid conversation trees.

### Product Goal

FlowForge is designed to create assistants that collaborate with users, not menus that constrain them.

The framework should preserve the natural flow of human conversation while remaining modular, configurable and reusable.

---

# Design Philosophy

FlowForge is designed around human conversation rather than rigid interaction trees.

People naturally move between topics during a conversation. They ask questions, return to previous subjects, interrupt themselves and continue where they left off.

FlowForge embraces this behavior instead of restricting it.

Capabilities are expected to collaborate by delegating control while preserving the Conversation Context.

The framework adapts to the user instead of forcing the user to adapt to the framework.

> **FlowForge is configured, not programmed.**

Business assistants should be created by composing reusable capabilities rather than writing custom conversation logic.

---

# Core Principles

1. The Engine must be reusable.
2. Business-specific logic must never be hardcoded.
3. Every assistant must be created through configuration.
4. Capabilities must be modular and independently reusable.
5. Connectors must remain isolated from conversation logic.
6. Actions must be reusable and independent.
7. Business knowledge must never be mixed with framework code.
8. Every component must have a single responsibility.
9. Conversation Context must always be preserved.

---

# Main Concepts

## Instance

A FlowForge Instance represents a complete conversational assistant for a single business.

Examples:

- Tarot reader
- Restaurant
- Clinic
- Lawyer
- Online shop

---

## Channel

A communication channel through which users interact with the assistant.

Examples:

- WhatsApp
- Web Widget
- Telegram
- REST API
- CLI

---

## Capability

A Capability is a reusable business behavior that can be enabled or disabled without modifying the Engine.

A Capability may include:

- Conversation flows
- Actions
- Knowledge
- Configuration
- Internal services
- Dependencies

Examples:

- FAQ
- Booking
- Lead Capture
- Human Transfer
- Payments
- Analytics

Capabilities collaborate with each other instead of competing for control of the conversation.

---

## Flow

A Flow represents a structured conversation inside a Capability.

Flows are local to a Capability and are responsible for completing a specific objective.

Examples:

- Booking Flow
- FAQ Flow
- Sales Flow
- Support Flow

Users are free to leave a Flow and return later without losing context.

---

## Action

An Action is an executable operation triggered during a conversation.

Actions perform work but never contain conversation logic.

Examples:

- Create Booking
- Cancel Booking
- Send Email
- Save Lead
- Transfer to Human
- Trigger Webhook

---

## Connector

A Connector integrates FlowForge with external platforms and services.

Connectors never contain business behavior.

They only provide communication with external systems.

Examples:

- WhatsApp
- Google Calendar
- SMTP
- Stripe
- Telegram
- Discord

---

## Knowledge

Knowledge represents all business-specific information consumed by the assistant.

Knowledge is never part of the framework itself.

Examples:

- Services
- Prices
- FAQs
- Opening Hours
- Policies
- Contact Information

---

## Conversation Context

Conversation Context represents everything the assistant currently knows about the ongoing conversation.

It includes:

- Current objective
- Active Capability
- Previous Capabilities
- Temporary user data
- Pending actions
- Conversation history
- Delegation state

Conversation Context must survive Capability transitions.

It should only be discarded when the conversation is explicitly reset.

---

# Target Architecture

```text
                        User
                          │
                          ▼
            Connector / Interface Layer
                          │
                          ▼
               FlowForge Application
                          │
                          ▼
            Conversation Orchestrator
                          │
                          ▼
               Capability Manager
                          │
      ┌───────────────────┼───────────────────┐
      │                   │                   │
      ▼                   ▼                   ▼
   Booking              FAQ          Lead Capture
      │                   │                   │
      └───────────────────┼───────────────────┘
                          ▼
                       Actions
                          ▼
                     Connectors
                          ▼
                 External Services
                          ▼
                       Response
```

---

# Architectural Principles

## FF-001

The Engine must never contain business-specific logic.

---

## FF-002

Every assistant must be created through configuration.

---

## FF-003

Capabilities must be self-contained and independently reusable.

---

## FF-004

Connectors must remain completely independent from the Engine.

---

## FF-005

Business knowledge must never be mixed with framework code.

---

## FF-006

Capabilities describe business behavior.

Connectors describe external integrations.

A Capability may depend on one or more Connectors, but a Connector is never a Capability.

---

## FF-007

Capabilities collaborate; they never compete.

A Capability should solve requests within its own domain.

When another Capability is better suited to handle a request, control should be delegated gracefully while preserving the Conversation Context.

---

## FF-008

Conversation Context must survive Capability transitions.

Users should never lose their original objective while navigating between Capabilities.

---

## FF-009

Capabilities collaborate through delegation, never through direct coupling.

Capabilities must not call each other directly.

Delegation is coordinated by the Conversation Orchestrator.

---

## FF-010

The Conversation Orchestrator coordinates the conversation.

Capabilities execute domain-specific behavior.

Connectors communicate with external systems.

Each component must focus exclusively on its own responsibility.

---

## FF-011

Every architectural component must have one clear responsibility and one reason to change.

This principle applies to every layer of the framework.

---

# Long-Term Vision

FlowForge should allow developers to build conversational assistants by composing reusable building blocks rather than writing custom implementations for each business.

Adding a new business should consist of configuring an Instance, selecting Capabilities, providing Knowledge and connecting external services.

The FlowForge Engine should remain unchanged regardless of the business domain.

Every new assistant should strengthen the framework instead of increasing its complexity.