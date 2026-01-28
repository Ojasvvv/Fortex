import copy
from typing import List, Any
from core.models import CapturedRequest
import uuid

class Mutator:
    @staticmethod
    def mutate(request: CapturedRequest) -> List[CapturedRequest]:
        """
        Generate deterministic mutations of a request.
        """
        mutants = []
        original_body = request.body
        
        # 1. Empty Body
        mutants.append(Mutator._create_mutant(request, None, "MUTATION_EMPTY_BODY"))
        
        # 2. Oversized Body (10KB junk)
        junk = "A" * 10240
        mutants.append(Mutator._create_mutant(request, junk, "MUTATION_OVERSIZED"))
        
        # 3. JSON Mutations (if body is dict)
        if isinstance(original_body, dict):
            # Drop fields one by one
            for key in original_body.keys():
                new_body = copy.deepcopy(original_body)
                del new_body[key]
                mutants.append(Mutator._create_mutant(request, new_body, f"MUTATION_MISSING_FIELD_{key}"))
                
                # Type Flip (int -> string)
                new_body_flip = copy.deepcopy(original_body)
                if isinstance(new_body_flip[key], int):
                    new_body_flip[key] = str(new_body_flip[key])
                elif isinstance(new_body_flip[key], str):
                    new_body_flip[key] = 12345
                mutants.append(Mutator._create_mutant(request, new_body_flip, f"MUTATION_TYPE_FLIP_{key}"))

        return mutants

    @staticmethod
    def _create_mutant(original: CapturedRequest, new_body: Any, tag: str) -> CapturedRequest:
        new_req = copy.deepcopy(original)
        new_req.request_id = f"{original.request_id}_{tag}_{uuid.uuid4().hex[:4]}"
        new_req.body = new_body
        # We might want to tag it in headers or metadata, but for now just ID
        return new_req
