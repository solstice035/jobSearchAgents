"""
CV Parser Agent

This agent provides CV parsing capabilities by integrating with the AdvancedCVParserService
to extract structured information from CVs/resumes.
"""

import io
import logging
from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..base_agent import BaseAgent
from ..protocols.agent_protocol import AgentCapability, AgentStatus
from ..message_bus import Message, MessageType, MessageBus
from services.advanced_cv_parser.advanced_cv_parser import (
    AdvancedCVParserService,
    CVParsingError,
)


class CVParserAgent(BaseAgent):
    """Agent that provides CV parsing capabilities by leveraging the AdvancedCVParserService"""

    def __init__(self, message_bus: MessageBus):
        """Initialize the CV parser agent"""
        # Setup logging first
        self.logger = logging.getLogger(__name__)

        # Initialize base agent
        super().__init__(agent_type="cv_parser", message_bus=message_bus)

        # Initialize thread pool for blocking operations
        self._executor = ThreadPoolExecutor(max_workers=3)

        # Get instance of CV parser service
        try:
            self.cv_parser = AdvancedCVParserService.get_instance()
            self.logger.info("Successfully initialized CV parser service")
        except Exception as e:
            self.logger.error(f"Failed to initialize CV parser service: {str(e)}")
            self.cv_parser = None

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensure cleanup"""
        self._executor.shutdown(wait=True)
        await super().__aexit__(exc_type, exc_val, exc_tb)

    def _register_capabilities(self):
        """Register the agent's capabilities"""
        self.register_capability(
            AgentCapability(
                name="parse_cv",
                description="Parse a CV/resume and extract structured information",
                parameters={
                    "file_content": "bytes",
                    "filename": "str",
                    "use_ai_enhancement": "bool",
                },
                required_resources=["document_parser"],
            )
        )

        self.register_capability(
            AgentCapability(
                name="get_supported_formats",
                description="Get list of supported CV file formats",
                parameters={},
                required_resources=[],
            )
        )

    async def initialize(self) -> bool:
        """Initialize the CV parser agent"""
        try:
            # Initialize base agent
            if not await super().initialize():
                return False

            # Verify CV parser service is available
            if not self.cv_parser:
                await self.update_status(
                    AgentStatus.ERROR, "CV parser service not available"
                )
                return False

            # Subscribe to relevant topics
            await self.subscribe_to_topic("cv.parse")
            await self.subscribe_to_topic("cv.formats")

            # Register capabilities
            self._register_capabilities()

            await self.update_status(AgentStatus.READY)
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize CV parser agent: {str(e)}")
            await self.update_status(AgentStatus.ERROR, str(e))
            return False

    async def handle_message(self, message: Message) -> Dict[str, Any]:
        """Handle incoming messages"""
        try:
            if message.message_type == MessageType.COMMAND:
                return await self._handle_command(message)
            elif message.message_type == MessageType.QUERY:
                return await self._handle_query(message)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported message type: {message.message_type}",
                }

        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _handle_command(self, message: Message) -> Dict[str, Any]:
        """Handle command messages"""
        if message.topic == "cv.parse":
            # Extract file content and filename from payload
            file_content = message.payload.get("file_content")
            filename = message.payload.get("filename")
            use_ai = message.payload.get("use_ai_enhancement", False)

            if not file_content or not filename:
                self.logger.warning("Missing required parameters in CV parse request")
                return {
                    "status": "error",
                    "error": "Missing required parameters: file_content and filename",
                }

            # Verify CV parser service is available
            if not self.cv_parser:
                self.logger.error("CV parser service not available")
                return {
                    "status": "error",
                    "error": "CV parser service not available",
                }

            # Verify file format is supported
            if not self.cv_parser.is_format_supported(filename):
                supported_formats = ", ".join(self.cv_parser.supported_formats)
                self.logger.warning(f"Unsupported file format for file: {filename}")
                return {
                    "status": "error",
                    "error": f"Unsupported file format. Supported formats: {supported_formats}",
                }

            # Update status to busy
            await self.update_status(AgentStatus.BUSY, "Parsing CV...")

            try:
                # Convert bytes to file-like object
                file_obj = io.BytesIO(file_content)

                # Run CV parsing in thread pool to avoid blocking
                loop = asyncio.get_running_loop()
                parsed_data = await loop.run_in_executor(
                    self._executor,
                    self._parse_cv_with_ai if use_ai else self.cv_parser.parse_cv,
                    file_obj,
                    filename,
                )

                # Update status back to ready
                await self.update_status(AgentStatus.READY)

                self.logger.info(f"Successfully parsed CV: {filename}")
                return {"status": "success", "data": parsed_data}

            except CVParsingError as e:
                error_msg = f"CV parsing error: {str(e)}"
                self.logger.error(error_msg)
                await self.update_status(AgentStatus.ERROR, error_msg)
                return {"status": "error", "error": str(e)}
            except Exception as e:
                error_msg = f"Unexpected error while parsing CV: {str(e)}"
                self.logger.error(error_msg, exc_info=True)  # Log full traceback
                await self.update_status(AgentStatus.ERROR, error_msg)
                return {"status": "error", "error": f"Failed to parse CV: {str(e)}"}

        return {
            "status": "error",
            "error": f"Unsupported command topic: {message.topic}",
        }

    def _parse_cv_with_ai(self, file_obj: io.BytesIO, filename: str) -> Dict[str, Any]:
        """Parse CV with AI enhancement enabled"""
        # Parse the CV using the service
        parsed_data = self.cv_parser.parse_cv(file_obj, filename)

        # Apply AI enhancements if available
        if hasattr(self.cv_parser, "enhance_parsed_data"):
            try:
                parsed_data = self.cv_parser.enhance_parsed_data(parsed_data)
                self.logger.info(f"Successfully applied AI enhancements to {filename}")
            except Exception as e:
                self.logger.warning(f"Failed to apply AI enhancements: {str(e)}")
                # Continue with unenhanced data

        return parsed_data

    async def _handle_query(self, message: Message) -> Dict[str, Any]:
        """Handle query messages"""
        if message.topic == "cv.formats":
            # Verify CV parser service is available
            if not self.cv_parser:
                self.logger.error("CV parser service not available for format query")
                return {
                    "status": "error",
                    "error": "CV parser service not available",
                }

            return {
                "status": "success",
                "data": {"supported_formats": self.cv_parser.supported_formats},
            }

        self.logger.warning(f"Unsupported query topic: {message.topic}")
        return {"status": "error", "error": f"Unsupported query topic: {message.topic}"}
